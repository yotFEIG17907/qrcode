import time

import signal
import adafruit_ws2801
import board
import numpy as np
import pyaudio
from numpy import linspace, frombuffer, ndarray, amax, multiply, clip, float32, delete, log10, hamming, float64, amin
from numpy.fft import fft, fftfreq
from scipy import average, log

# FFT On the microphone input plus LEDS
# Based on this https://bitbucket.org/togiles/lightshowpi/src/master/py/fft.py
# and this: https://jared.geek.nz/2013/jan/sound-reactive-led-lights

debug = True

# Set up for the LEDs
SDI = board.MOSI
CLK = board.SCLK
bright = 1.0

# Configure the count of pixels:
num_pixels = 100

pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=num_pixels, brightness=bright, auto_write=False)

def handler(signum, frame):
    pixels.fill((0, 0, 0))
    pixels.show()
    exit(1)

# Turn all the LEDs off on CTRL-C and terminate
signal.signal(signal.SIGINT, handler)


# Check the LEDs light up
pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)
for i in range(num_pixels):
    pixels[i] = (255, 0, 0)
    pixels.show()
    time.sleep(0.01)
for i in range(num_pixels):
    pixels[i] = (0, 255, 0)
    pixels.show()
    time.sleep(0.01)
for i in range(num_pixels):
    pixels[i] = (0, 0, 255)
    pixels.show()
    time.sleep(0.01)
pixels.fill((0, 0, 0))
pixels.show()


# This is the index of the microphone
input_device_index = 2

# Set up audio sampler
# Number of samples needs to be a power of 2.
NUM_SAMPLES = 2 ** 10
# Not sure what determines this or what other values are possible.
SAMPLING_RATE = 44100
time_step = 1.0 / SAMPLING_RATE
max_freq = SAMPLING_RATE // 2
total_bins = NUM_SAMPLES // 2

def get_bin_for_freq(freq: float):
    return int(total_bins * freq / max_freq)

cutoff_bin = get_bin_for_freq(8000)
# if you take an FFT of a chunk of audio, the edges will look like
# super high frequency cutoffs. Applying a window tapers the edges
# of each end of the chunk down to zero.
hamming_window = hamming(NUM_SAMPLES).astype(float32)

pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=SAMPLING_RATE,
                 input_device_index=input_device_index,
                 input=True,
                 output=False,
                 frames_per_buffer=NUM_SAMPLES)

print("Spectrum Analyzer working. Press CTRL-C to quit.")

# Creates and array of NUM_SAMPLES/2 spread equally over the range
# from 0 to half the sampling rate. Essentially these are the frequency total_bins
# The frequency for any intensity value can be found by getting the
# index of that intensity bin and looking up the value in the corresponding
# bin in the frequencies array.
# This has only positive frequencies because of how the intensity is calculated
frequencies = linspace(0.0, float(SAMPLING_RATE) / 2, num=NUM_SAMPLES // 2)

# fftfreq includes positive and negative frequencies
# frequencies = fftfreq(NUM_SAMPLES*2, 1.0/SAMPLING_RATE)

def get_fft(data: ndarray):
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
    freq = fftfreq(len(FFT), 1.0/SAMPLING_RATE)
    return freq[:len(freq)//2], FFT[:len(FFT)//2]


reporting_bands_interval = 10000
reporting_fps_interval = 10000
counter = 0
# Note: For Python3 use // when dividing int by int to get an int

start_time = time.time()
while True:
    counter += 1
    # Need to set exception on overflow false, because this cannot keep up
    # with the data rate
    data = stream.read(NUM_SAMPLES, exception_on_overflow=False)
    audio_data = frombuffer(data, 'int16')
    freqs, intensity = get_fft(audio_data)
    # average the intensity over frequency (audio frequency) bands chosen for aesthetic qualities,
    # these bands will be mapped to color ranges, e.g. RED, GREEN and BLUE.
    # In other words: Bass, mid-range and treble are mapped to Red/Green/Blue
    # Color is determined by the band and the brightness by the intensity. These
    # bands are chosen by trial and error. Then these intensity values are mapped to
    # sections of the LED strand. There are several factors here, ultimately the LEDs
    # need to look pleasing to the eye and must be clearly in sync with the music. Complicated
    # by the fact that the frequency bands are not the same width.
    # intensity_slices = [average(intensity[s]) for s in audio_bands]
    # Another approach, pick the maximum
    # intensity_slices = [amax(intensity[s]) for s in audio_bands]
    # Another approach, pick the same number of bands as there are LEDs
    N = cutoff_bin // num_pixels
    sig_threshold = float64(70000.0)
    upper_threshold = float64(150000.0)
    intensity[intensity < sig_threshold] = 0
    intensity_slices = [average(intensity[n:n + N]) for n in range(10, cutoff_bin, N)]
    intensity_slices = intensity_slices[0:num_pixels]
    sig_average = average(intensity_slices)
    max = amax(intensity_slices)
    min = amin(intensity_slices)
    print(f"{min:10.1f} {sig_average: 10.1f} {max: 10.1f}", "\r", flush=True, end='')
    intensity_slices = ((intensity_slices / max) * 255).astype(np.int)
    # Need to limit the values to between 0 and 255
    intensity_slices = clip(intensity_slices, 0, 255)
    # Threshold
    average_intensity = average(intensity_slices)
    pixel_max = amax(intensity_slices)
    threshold = int(average_intensity * 2.6)
    intensity_slices[intensity_slices < threshold] = 0
    band0_stop = len(intensity_slices) // 3
    band1_stop = band0_stop * 2
    band2_stop = len(intensity_slices)
    for i, value in np.ndenumerate(intensity_slices):
        index = i[0]
        if band0_stop > index:
            pixels[index] = (value, 0, 0)
        elif band1_stop > index:
            pixels[index] = (0, value, 0)
        elif band2_stop > index:
            pixels[index] = (0, 0, value)
        else:
            pixels[index] = (value, value, value)
    pixels.show()

    # Report intensity
    if counter % reporting_bands_interval == 0:
        print(len(intensity_slices), len(freqs), "Max (", max, ")", "Min (", min, ")", "Average (", average_intensity, ")",
              "Threshold (", threshold, ")",
                  intensity_slices)

    # Report the frames per second
    if counter % reporting_fps_interval == 0:
        lap = time.time()
        elapsed = lap - start_time
        start_time = lap
        loops_per_second = reporting_fps_interval / elapsed
        print("Elapsed time", elapsed, "Frames per second", loops_per_second)
