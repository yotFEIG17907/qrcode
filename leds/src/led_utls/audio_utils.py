"""
Using librosa, real-time
https://stackoverflow.com/questions/59056786/python-librosa-with-microphone-input
"""

import time

import librosa
import numpy as np
import pyaudio
from librosa import display
from matplotlib import pyplot as plt


class AudioHandler(object):
    def __init__(self, input_device_index: int, CHANNELS: int, RATE: int, CHUNK: int):
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = CHANNELS
        self.RATE = RATE
        self.CHUNK = CHUNK
        self.input_device_index = input_device_index
        self.p = None
        self.stream = None
        self.numpy_array = None
        fig, ax = plt.subplots(nrows=1, sharex=True)
        self.ax = ax

    def start(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input_device_index=self.input_device_index,
                                  input=True,
                                  output=False,
                                  stream_callback=self.callback,
                                  frames_per_buffer=self.CHUNK)

    def callback(self, in_data, frame_count, time_info, flag):
        self.numpy_array = np.frombuffer(in_data, dtype=np.float32)
        mfcc = librosa.feature.mfcc(self.numpy_array)
        return None, pyaudio.paContinue

    def shutdown(self):
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.p.terminate()
        self.p = None

    def mainloop(self):
        while (self.stream.is_active()):
            # if using button you can set self.stream to 0 (self.stream = 0),
            # otherwise you can use a stop condition
            print("Stream is active")
            if self.numpy_array is not None:
                display.waveshow(y=self.numpy_array, sr=self.RATE,
                                 max_points=self.RATE // 2,
                                 ax=self.ax)
                plt.clf()
                plt.show(block=False)
                plt.pause(0.0001)
            #time.sleep(2.0)
