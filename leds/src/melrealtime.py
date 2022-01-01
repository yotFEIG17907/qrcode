import time

"""
This uses librosa library to generate and display a MEL Spectrogram.
To view the display run it in a terminal, "python melrealtime.py"

Takes audio input from the microphone.
"""

import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pyaudio

rate = 22050
chunk_size = rate // 4

lavalier_mike_index = 2

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=lavalier_mike_index,
                frames_per_buffer=chunk_size)

frames = []

plt.figure(figsize=(10, 4))
do_melspec = librosa.feature.melspectrogram
pwr_to_db = librosa.core.power_to_db

while True:

    start = time.time()

    data = stream.read(chunk_size, exception_on_overflow=False)
    data = np.frombuffer(data, dtype=np.float32)

    # Map into 100 bins so it can eventually be displayed on the 100 LED strand.
    # melspec = do_melspec(y=data, sr=rate, n_mels=128, fmax=8000)
    melspec = do_melspec(y=data, sr=rate, n_mels=100, fmax=8000)
    norm_melspec = pwr_to_db(melspec, ref=np.max)

    frames.append(norm_melspec)

    # Note: the display won't appear until first 20 frames have been processed.
    if len(frames) == 20:
        stack = np.hstack(frames)

        librosa.display.specshow(stack, y_axis='mel', fmax=8000, x_axis='time')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Mel spectrogram')
        plt.draw()
        plt.pause(0.0001)
        plt.clf()
        # break
        frames.pop(0)

    t = time.time() - start

    print(1 / t)
