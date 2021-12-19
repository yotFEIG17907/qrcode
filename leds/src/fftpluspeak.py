import signal
import time

import adafruit_ws2801
import board
import numpy as np
import pyaudio
from numpy import linspace, frombuffer, ndarray, amax, clip, float32, float64, hamming, log10, array
from numpy.fft import fft, fftfreq
from scipy import average

# FFT On the microphone input plus LEDS
# Based on this https://bitbucket.org/togiles/lightshowpi/src/master/py/fft.py
# and this: https://jared.geek.nz/2013/jan/sound-reactive-led-lights
#
# This will peak detection on the FFT

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
max_freq_hz = SAMPLING_RATE // 2
total_bins = NUM_SAMPLES // 2
# Split the bands into 3. This defines the slices for each band
# bass 20 to 300 Hz, mid-range 300 Hz to 4 kHz, treble 4 kHz to the end.
# There are NUM_SAMPLES equal width bins, covering frequency range from 0 - SAMPLING_RATE/2
bass_lower_freq_hz = 0
base_upper_freq_hz = 299
mid_range_lower_freq_hz = 350
mid_range_upper_freq_hz = 3000
treble_lower_freq_hz = 4000
treble_upper_freq_hz = max_freq_hz
cutoff_freq_hz = 8000
bins_per_hz = total_bins / max_freq_hz
# Convert the frequency in Hertz to bins in the FFT.
bass = slice(int(bass_lower_freq_hz * bins_per_hz), int(base_upper_freq_hz * bins_per_hz))
mid_range = slice(int(mid_range_lower_freq_hz * bins_per_hz), int(mid_range_upper_freq_hz * bins_per_hz))
treble = slice(int(treble_lower_freq_hz * bins_per_hz), total_bins)
audio_bands = [bass, mid_range, treble]
print("BANDS", audio_bands)

def get_bin_for_freq(freq: float):
    return int(bins_per_hz * freq)

cutoff_bin = get_bin_for_freq(cutoff_freq_hz)

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
    freq = fftfreq(len(FFT), 1.0 / SAMPLING_RATE)
    return freq[:len(freq) // 2], FFT[:len(FFT) // 2]


reporting_bands_interval = 10000
reporting_fps_interval = 400
counter = 0
# Note: For Python3 use // when dividing int by int to get an int

a_third = num_pixels // 3
band0_stop = a_third
band1_stop = band0_stop * 2
band2_stop = num_pixels

start_time = time.time()
while True:
    # Need to set exception on overflow false, because this cannot keep up
    # with the data rate
    data = stream.read(NUM_SAMPLES, exception_on_overflow=False)
    audio_data = frombuffer(data, 'int16')
    freqs, intensity_raw = get_fft(audio_data)
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
    max = array([max(intensity[s]) for s in audio_bands])
    threshold = sig_average * float64(1.5)
    intensity[intensity < threshold] = 0
    # Map number of bins to the array pixels and values to the range 0 to 255
    N = cutoff_bin // num_pixels
    intensity_slices = [average(intensity[n:n + N]) for n in range(10, cutoff_bin, N)]
    intensity_slices = intensity_slices[0:num_pixels]
    intensity_slices = ((intensity_slices / max) * 255).astype(np.int)
    # Need to limit the values to between 0 and 255
    intensity_slices = clip(intensity_slices, 0, 255)
    pixels.fill((0, 0, 0))
    for i in range(num_pixels):
        if i < band0_stop:
            color = (255, 0, 0)
        elif i < band1_stop:
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)
        if intensity_slices[i] > 0:
            pixels[i] = color
    pixels.show()

    # Report the frames per second
    if counter % reporting_fps_interval == 0:
        lap = time.time()
        elapsed = lap - start_time
        start_time = lap
        loops_per_second = reporting_fps_interval / elapsed
        print("Elapsed time", elapsed, "Frames per second", loops_per_second)
        print("average", sig_average, "Intensity", intensity)
    counter += 1
