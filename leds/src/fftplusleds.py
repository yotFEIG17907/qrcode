import numpy as np
import time

import pyaudio
from numpy import linspace, frombuffer, ndarray, amax
from scipy import average
from scipy.fftpack import fft
import board
import adafruit_ws2801
# FFT On the microphone input plus LEDS

debug = True

# Set up for the LEDs
SDI = board.MOSI
CLK = board.SCLK
bright = 1.0

# Configure the count of pixels:
num_pixels = 100

pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=num_pixels, brightness=bright, auto_write=False)
print("Fill 255")
pixels.fill((255,0,0))
pixels.show()
time.sleep(0.1)
print("Fill next")
pixels.fill((0,255,0))
pixels.show()
time.sleep(0.1)
print("And next..")
pixels.fill((0,0,255))
pixels.show()
time.sleep(0.1)
pixels.fill((0,0,0))
pixels.show()
time.sleep(0.1)
for i in range(num_pixels):
    pixels[i] = (255,0,0)
    pixels.show()
    time.sleep(0.05)
pixels.fill((0,0,0))
pixels.show()

# This is the index of the microphone
input_device_index = 2

# Set up audio sampler
# Number of samples needs to be a power of 2.
NUM_SAMPLES = 2**10
# Not sure what determines this or what other values are possible.
SAMPLING_RATE = 44100
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
# from 0 to half the sampling rate. Essentially these are the frequency bins
# The frequency for any intensity value can be found by getting the
# index of that intensity bin and looking up the value in the corresponding
# bin in the frequencies array.
# This has only positive frequencies because of how the intensity is calculated
frequencies = linspace(0.0, float(SAMPLING_RATE) / 2, num=NUM_SAMPLES // 2)
# fftfreq includes positive and negative frequencies
#frequencies = fftfreq(NUM_SAMPLES*2, 1.0/SAMPLING_RATE)

def get_fft(data: ndarray):
    """
    Computes the FFT on the data, normalizing it first and then taking only
    the 1st half of the FFT and taking the absolute value
    :param data: The signal in the time domain, i.e. an array of samples spaced
    by equal time intervals
    :returns A tuple: an array of the frequencies and the corresponding array of intensities.
    """
    # Each data point is a signed 16 bit number, so we can normalize by dividing 32*1024
    normalized_data = audio_data / 32768.0
    intensity = abs(fft(normalized_data))[:NUM_SAMPLES // 2]
    return frequencies, intensity


reporting_bands_interval = 100
reporting_fps_interval = 100
counter = 0
# Note: For Python3 use // when dividing int by int to get an int

# Split the bands into 3. This defines the slices for each band
# bass 20 to 300 Hz, mid-range 300 Hz to 4 kHz, treble 4 kHz to the end.
# There are NUM_SAMPLES equal width bins, covering frequency range from 0 - SAMPLING_RATE/2
max_freq = SAMPLING_RATE // 2
bin_freq_width = (NUM_SAMPLES // 2)/ max_freq
bass = slice(1, int(299 * bin_freq_width))
mid_range = slice(int(350 * bin_freq_width), int(3000 * bin_freq_width))
treble = slice(int(4000 * bin_freq_width), NUM_SAMPLES // 2)
audio_bands = [bass, mid_range, treble]

print("BANDS", audio_bands)

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
    #intensity_slices = [average(intensity[s]) for s in audio_bands]
    # Another approach, pick the maximum
    # intensity_slices = [amax(intensity[s]) for s in audio_bands]
    # Another approach, pick the same number of bands as there are LEDs
    N = (NUM_SAMPLES // 2) // num_pixels
    intensity_slices = [average(intensity[n:n+N]) for n in range(1, len(intensity), N)]
    intensity_slices = intensity_slices[0:num_pixels]
    max_intensity = amax(intensity_slices)
    intensity_slices = ((intensity_slices / max_intensity) * 255).astype(np.int)
    # Threshold
    threshold = 40
    intensity_slices[intensity_slices < threshold] = 0
    for i, value in np.ndenumerate(intensity_slices):
        pixels[i[0]] = (value, value, value)
    pixels.show()
    # Report intensity
    if counter % reporting_bands_interval == 0:
        print(len(intensity_slices), len(freqs), intensity_slices)

    # Report the frames per second
    if counter % reporting_fps_interval == 0:
        lap = time.time()
        elapsed = lap - start_time
        start_time = lap
        loops_per_second = reporting_fps_interval / elapsed
        print("Elapsed time", elapsed, "Frames per second", loops_per_second)