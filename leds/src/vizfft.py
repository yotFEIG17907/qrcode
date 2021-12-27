"""
Audio Spectrum Analyzer from https://www.youtube.com/watch?v=AShHJdSIxkY

With modifications to make it work on OSX - Catalina
"""
import signal
import time

import matplotlib.pyplot as plt
import numpy as np
import pyaudio
# Number of samples
from numpy import frombuffer, amax
from scipy.fftpack import fft


def initialize_shutdown_handler(pa=None, stream=None):
    # stop the stream, close it, and terminate the pyaudio instantiation
    def handler(signum, frame):
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if pa is not None:
            pa.terminate()
        exit(1)

    # Turn all the LEDs off on CTRL-C and terminate
    signal.signal(signal.SIGINT, handler)


LAVALIER_MIKE = 2
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
# Sample rate 44.1 kHz
RATE = 44100

# Setting up the audio source. The YouTube guy says
# to supply output=True but when I did that all the
# values read were zero
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=False,
                    frames_per_buffer=CHUNK,
                    input_device_index=LAVALIER_MIKE)

initialize_shutdown_handler(pa=audio, stream=stream)

# Plot the chunk of data just read
fig, (ax1, ax2) = plt.subplots(2, figsize=(15, 7))
x = np.arange(0, CHUNK)  # Audio Time domain
xf = np.linspace(0, RATE, CHUNK) # Frequency domain, the spectrum

line, = ax1.plot(x, np.random.rand(CHUNK), '-', lw=2)
line_fft, = ax2.semilogx(xf, np.random.rand(CHUNK), '-', lw=2)

peaks = 10000
ax1.set_title('AUDIO WAVEFORM')
ax1.set_xlabel('samples')
ax1.set_ylabel('volume')
ax1.set_ylim(-peaks, peaks)
ax1.set_xlim(0, CHUNK)

ax2.set_xlim(20, RATE/2)
ax2.set_ylim(0, 50)

overflow = False
print("Starting to read chunks overflow?", overflow, flush=True)
report_fps = 1000
frame_count = 0
start_time = time.time()
while True:
    # Read a chunk and convert to integers.
    data = stream.read(CHUNK, exception_on_overflow=overflow)
    data_int = frombuffer(data, 'int16')
    FFT = fft(data_int) + 0.0000001
    # Amplitude/Power
    # This will blow up if any values of the FFT are zero
    levels = np.log10(np.abs(FFT)) ** 2
    line_fft.set_ydata(levels)
    line.set_ydata(data_int)
    plt.show(block=False)
    # Found it is necessary to pause or the plot won't show
    plt.pause(0.0001)
    frame_count = frame_count + 1
    if frame_count % report_fps == 0:
        end_time = time.time()
        print("Frame rate", frame_count / (end_time - start_time))
        start_time = end_time
