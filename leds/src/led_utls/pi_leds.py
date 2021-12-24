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


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)


def rainbow_cycle(pixels, num_pixels, wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)
