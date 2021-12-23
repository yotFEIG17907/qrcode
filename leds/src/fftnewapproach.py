import signal
import time
from typing import Tuple, List

import adafruit_ws2801
import board
import numpy as np
import pyaudio
from numpy import frombuffer, ndarray, float32, hamming, clip, amax, average
from numpy.fft import fft
# FFT On the microphone input plus LEDS
# Handling of the peaks based on this: https://github.com/yotFEIG17907/addressable-leds/wiki
from scipy.linalg._solve_toeplitz import float64

from leds.src.led_utls.nm_to_rgb import wavelength_to_rgb_factor

debug = True


def initialize_leds(n: int, brightness: float):
    # Set up for the LEDs
    SDI = board.MOSI
    CLK = board.SCLK
    pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=n, brightness=brightness, auto_write=False)
    return pixels


def initialize_shutdown_handler(pixels, pa, stream):
    def handler(signum, frame):
        pixels.fill((0, 0, 0))
        pixels.show()
        stream.stop_stream()
        stream.close()
        pa.terminate()
        exit(1)

    # Turn all the LEDs off on CTRL-C and terminate
    signal.signal(signal.SIGINT, handler)


def show_all_leds(pixels):
    # Check the LEDs light up
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(0.1)
    n_pixels = len(pixels)
    for i in range(n_pixels):
        pixels[i] = (255, 0, 0)
        pixels.show()
        time.sleep(0.01)
    pixels.fill((0, 0, 0))
    pixels.show()


def initialize_audio(sampling_rate: int, input_device_index: int, samples_per_buffer: int):
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=sampling_rate,
                     input_device_index=input_device_index,
                     input=True,
                     output=False,
                     frames_per_buffer=samples_per_buffer)
    return pa, stream


def get_fft(data: ndarray, window):
    """
    Computes the FFT on the data, normalizing it first and then taking only
    the 1st half of the FFT and taking the absolute value
    :param data: The signal in the time domain, i.e. an array of samples spaced
    by equal time intervals
    :returns A tuple: an array of the frequencies and the corresponding array of intensities.
    """
    data = data * window
    FFT = fft(data)
    # Amplitude/Power
    # Cannot take log because some values are zero
    amp = np.abs(FFT)
    # Only 1st half is real
    return amp[:len(amp) // 2]


def get_color_map(n_bins: int) -> List[Tuple[float, float, float]]:
    """
    Generates an array of colors to cover the visible spectrum with the given number of bins
    :param n_bins: The number of distinct colors
    :return: A list of color tuples, RGB factors (from 0 to 1)
    """
    step = (380 - 750) / n_bins
    colors = []
    for wavelength in np.arange(750, 380, step):
        colors.append(wavelength_to_rgb_factor(wavelength=wavelength, gamma=1.0))
    assert len(colors) == n_bins, f"Colors length is {len(colors)} but n_bins is {n_bins}"
    return colors


def do_fft_loop(stream, pixels, cutoff_freq_hz: float, window, sample_rate: int, n_samples: int) -> None:
    """

    :param stream: The source of audio samples
    :param pixels: The pixels to be controlled
    :param cutoff_freq_hz: The highest frequency to use
    :param window: The Window to apply to data to "feather" the edges
    :param sample_rate: The rate at which the audio is sampled
    :param n_samples: How samples or bins, this determined how many frequency bins are in the FFT
    :return: Nothing
    """
    reporting_fps_interval = 400
    # Note: For Python3 use // when dividing int by int to get an int
    max_led_value = int(255)
    num_pixels = len(pixels)
    counter = 0
    start_time = time.time()
    # Limit the top frequency
    hz_per_bin = (sample_rate / 2) / (n_samples / 2)
    max_freq = cutoff_freq_hz
    cutoff_bin = int(max_freq / hz_per_bin)
    # Then want cutoff bin to a multiple of the number of pixels but it must be a minimum of 1
    N = max(1, cutoff_bin // num_pixels)
    cutoff_bin = N * num_pixels
    color_factors = get_color_map(num_pixels)
    while True:
        # Need to set exception on overflow false, because this cannot keep up
        # with the data rate
        data = stream.read(n_samples, exception_on_overflow=False)
        audio_data = frombuffer(data, 'int16')
        levels = get_fft(data = audio_data, window=window)
        # Truncate to the cutoff frequency
        levels = levels[:-(len(levels) - cutoff_bin)]
        # Map the levels an intensity and threshold
        max_level = amax(levels)
        if max_level == 0.0:
            print("Max level is zero")
            continue
        threshold = average(levels) * 1.8
        levels[levels < threshold] = 0.0
        # Split the array into groups of N in size and compute the mean of each group.
        level_slices = levels.reshape(-1, N).mean(axis=1)
        # Normalized these onto the range 0 to 255.0
        matrix = np.int_(level_slices * float64(max_led_value / max_level))
        # Need to limit the values to between 0 and the max LED value
        matrix = clip(matrix, 0, max_led_value)
        # Limit it to only num pixels
        matrix = matrix[0:num_pixels]

        pixels.fill((0, 0, 0))
        for i in range(num_pixels):
            level = matrix[i]
            color = ([int(rgb_factor * level) for rgb_factor in color_factors[i]])
            pixels[i] = color
        pixels.show()

        # Report the frames per second
        if counter % reporting_fps_interval == 0:
            lap = time.time()
            elapsed = lap - start_time
            start_time = lap
            loops_per_second = reporting_fps_interval / elapsed
            print("Elapsed time", elapsed, "Frames per second", loops_per_second)
            print("Levels", len(levels), levels, "matrix", len(matrix), matrix)
        counter += 1


def main():
    # Configure the count of pixels:
    num_pixels = 100

    # This is the index of the microphone
    input_device_index = 2

    # Set up audio sampler
    # Number of bins in the FFT needs to be a power of 2
    NUM_SAMPLES = 512
    # Not sure what determines this or what other values are possible.
    SAMPLING_RATE = 44100

    cutoff_freq_hz = 10000
    pixels = initialize_leds(n=num_pixels, brightness=1.0)
    print("LEDs initialized")
    pa, stream = initialize_audio(sampling_rate=SAMPLING_RATE, input_device_index=input_device_index,
                              samples_per_buffer=NUM_SAMPLES)
    print("Audio input initialized")
    initialize_shutdown_handler(pixels, pa, stream)
    show_all_leds(pixels)
    print("Spectrum Analyzer starting. Press CTRL-C to quit.")

    # if you take an FFT of a chunk of audio, the edges will look like
    # super high frequency cutoffs. Applying a window tapers the edges
    # of each end of the chunk down to zero.
    hamming_window = hamming(NUM_SAMPLES).astype(float32)

    do_fft_loop(stream,
                pixels,
                window=hamming_window,
                cutoff_freq_hz=cutoff_freq_hz,
                sample_rate=SAMPLING_RATE,
                n_samples=NUM_SAMPLES)


if __name__ == "__main__":
    main()
