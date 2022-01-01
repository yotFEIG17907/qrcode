"""
Using the Librosa package
"""
import signal

from led_utls.audio_utils import AudioHandler


def initialize_shutdown_handler(pa: AudioHandler):
    # stop the stream, close it, and terminate the pyaudio instantiation
    def handler(signum, frame):
        pa.shutdown()
        exit(1)

    # Turn all the LEDs off on CTRL-C and terminate
    signal.signal(signal.SIGINT, handler)


def main():
    lavalier_mike = 2
    channels = 1
    rate = 44100
    CHUNK = 1024 * 2
    audio = AudioHandler(input_device_index=lavalier_mike,
                         CHANNELS=channels,
                         RATE=rate,
                         CHUNK=CHUNK)
    audio.start()  # open the the stream
    audio.mainloop()  # main operations with librosa
    audio.stop()


if __name__ == "__main__":
    main()
