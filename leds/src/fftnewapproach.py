import signal
import time

import adafruit_ws2801
import board
import numpy as np
import pyaudio
from numpy import linspace, frombuffer, ndarray, clip, float32, float64, hamming, log10, array
from numpy.fft import fft, fftfreq
from scipy import average, amax

# FFT On the microphone input plus LEDS
# Handling of the peaks based on this: https://github.com/yotFEIG17907/addressable-leds/wiki

debug = True


def initialize_leds(n: int, brightness: float):
    # Set up for the LEDs
    SDI = board.MOSI
    CLK = board.SCLK
    pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=n, brightness=brightness, auto_write=False)
    return pixels


def initialize_shutdown_handler(pixels):
    def handler(signum, frame):
        pixels.fill((0, 0, 0))
        pixels.show()
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


time_step = 1.0 / SAMPLING_RATE
max_freq_hz = SAMPLING_RATE // 2
total_bins = NUM_SAMPLES // 2
# Split the bands into 3. This defines the slices for each band
# bass 20 to 300 Hz, mid-range 300 Hz to 4 kHz, treble 4 kHz to the end.
# There are NUM_SAMPLES equal width bins, covering frequency range from 0 - SAMPLING_RATE/2
bass_lower_freq_hz = 0
base_upper_freq_hz = 999
mid_range_lower_freq_hz = 1000
mid_range_upper_freq_hz = 3999
treble_lower_freq_hz = 4000
treble_upper_freq_hz = max_freq_hz
cutoff_freq_hz = 8000
bins_per_hz = total_bins / max_freq_hz
# Convert the frequency in Hertz to bins in the FFT.
bass = slice(int(bass_lower_freq_hz * bins_per_hz), int(base_upper_freq_hz * bins_per_hz))
mid_range = slice(int(mid_range_lower_freq_hz * bins_per_hz), int(mid_range_upper_freq_hz * bins_per_hz))
treble = slice(int(treble_lower_freq_hz * bins_per_hz), total_bins)
# Audio bands is a list of slices of the FFT array.
audio_bands = [bass, mid_range, treble]

band0_stop = int(bass.stop * num_pixels / total_bins)
band1_stop = int(mid_range.stop * num_pixels / total_bins)
band2_stop = int(treble.stop * num_pixels / total_bins)


def get_bin_for_freq(freq: float):
    return int(bins_per_hz * freq)


cutoff_bin = get_bin_for_freq(cutoff_freq_hz)

# if you take an FFT of a chunk of audio, the edges will look like
# super high frequency cutoffs. Applying a window tapers the edges
# of each end of the chunk down to zero.
hamming_window = hamming(NUM_SAMPLES).astype(float32)


def initialize_audio(sampling_rate: int, input_device_index: int, samples_per_buffer: int)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=sampling_rate,
                     input_device_index=input_device_index,
                     input=True,
                     output=False,
                     frames_per_buffer=samples_per_buffer)
    return stream


# Creates and array of NUM_SAMPLES/2 spread equally over the range
# from 0 to half the sampling rate. Essentially these are the frequency total_bins
# The frequency for any intensity value can be found by getting the
# index of that intensity bin and looking up the value in the corresponding
# bin in the frequencies array.
# This has only positive frequencies because of how the intensity is calculated
frequencies = linspace(0.0, float(SAMPLING_RATE) / 2, num=NUM_SAMPLES // 2)


# fftfreq includes positive and negative frequencies
# frequencies = fftfreq(NUM_SAMPLES*2, 1.0/SAMPLING_RATE)

def get_fft(data: ndarray, sample_rate: int):
    """
    Computes the FFT on the data, normalizing it first and then taking only
    the 1st half of the FFT and taking the absolute value
    :param data: The signal in the time domain, i.e. an array of samples spaced
    by equal time intervals
    :returns A tuple: an array of the frequencies and the corresponding array of intensities.
    """
    data = data * hamming_window
    FFT = fft(data)
    FFT = abs(FFT)
    # Only the 1st half are real
    freq = fftfreq(len(FFT), 1.0 / sample_rate)
    return freq[:len(freq) // 2], FFT[:len(FFT) // 2]


print("BANDS", audio_bands)


def do_fft_loop(stream, pixels, sample_rate: int, n_samples):
    reporting_bands_interval = 10000
    reporting_fps_interval = 400
    counter = 0
    # Note: For Python3 use // when dividing int by int to get an int
    num_pixels = len(pixels)
    counter = 0
    start_time = time.time()
    while True:
        # Need to set exception on overflow false, because this cannot keep up
        # with the data rate
        data = stream.read(n_samples, exception_on_overflow=False)
        audio_data = frombuffer(data, 'int16')
        freqs, intensity_raw = get_fft(audio_data, sample_rate=sample_rate)
        # average the intensity over frequency (audio frequency) bands chosen for aesthetic qualities,
        # these bands will be mapped to color ranges, e.g. RED, GREEN and BLUE.
        # In other words: Bass, mid-range and treble are mapped to Red/Green/Blue
        # Color is determined by the band and the brightness by the intensity. These
        # bands are chosen by trial and error. Then these intensity values are mapped to
        # sections of the LED strand. There are several factors here, ultimately the LEDs
        # need to look pleasing to the eye and must be clearly in sync with the music. Complicated
        # by the fact that the frequency bands are not the same width.
        # Use the log10 of the intensity
        intensity = log10(intensity_raw)
        # Compute the average in each of the bands separately
        sig_average = array([average(intensity[s]) for s in audio_bands])
        band_max = array([amax(intensity[s]) for s in audio_bands])
        band_thresholds = sig_average * float64(1.3)
        # Apply each band's threshold to its slice of the array
        for band_threshold, band_slice in zip(band_thresholds, audio_bands):
            intensity[band_slice] = np.where(intensity[band_slice] < band_threshold, 0, intensity[band_slice])
        # Map the intensity to the range 0-255
        for max, band_slice in zip(band_max, audio_bands):
            intensity_slices = ((intensity[band_slice] / max) * 255).astype(np.int)
        # Map the FFT bands onto the pixels.
        N = cutoff_bin // num_pixels
        intensity_slices = [int(average(intensity_slices[n:n + N])) for n in range(10, cutoff_bin, N)]
        intensity_slices = intensity_slices[0:num_pixels]
        # Need to limit the values to between 0 and 255
        intensity_slices = clip(intensity_slices, 0, 255)
        pixels.fill((0, 0, 0))
        for i in range(num_pixels):
            pixel_brightness = intensity_slices[i]
            if pixel_brightness > 0:
                if i < band0_stop:
                    color = (pixel_brightness, 0, 0)
                elif i < band1_stop:
                    color = (0, pixel_brightness, 0)
                else:
                    color = (0, 0, pixel_brightness)
                pixels[i] = color
        pixels.show()

        # Report the frames per second
        if counter % reporting_fps_interval == 0:
            lap = time.time()
            elapsed = lap - start_time
            start_time = lap
            loops_per_second = reporting_fps_interval / elapsed
            print("Elapsed time", elapsed, "Frames per second", loops_per_second)
            print("average", sig_average, "Intensity", intensity_slices)
        counter += 1


def main():
    # Configure the count of pixels:
    num_pixels = 100

    # This is the index of the microphone
    input_device_index = 2

    # Set up audio sampler
    # Number of samples needs to be a power of 2.
    NUM_SAMPLES = 2 ** 10
    # Not sure what determines this or what other values are possible.
    SAMPLING_RATE = 44100

    pixels = initialize_leds(n=num_pixels, brightness=1.0)
    print("LEDs initialized")
    stream = initialize_audio(sampling_rate=SAMPLING_RATE, input_device_index=input_device_index,
                              samples_per_buffer=NUM_SAMPLES)
    print("Audio input initialized")
    show_all_leds(pixels)
    print("Spectrum Analyzer starting. Press CTRL-C to quit.")

    do_fft_loop(stream, pixels, sample_rate=SAMPLING_RATE)


if __name__ == "__main__":
    main()
