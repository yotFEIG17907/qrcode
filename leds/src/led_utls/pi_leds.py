import signal
import time

import adafruit_ws2801
import board


def initialize_leds(n: int, brightness: float):
    # Set up for the LEDs
    SDI = board.MOSI
    CLK = board.SCLK
    pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=n, brightness=brightness, auto_write=False)
    return pixels


def leds_cleanup(pixels):
    pixels.fill((0, 0, 0))
    pixels.show()


def initialize_shutdown_handler(pixels, pa=None, stream=None):
    def handler(signum, frame):
        leds_cleanup(pixels)
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if pa is not None:
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
