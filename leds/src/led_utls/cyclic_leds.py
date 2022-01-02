# Simple demo of of the WS2801/SPI-like addressable RGB LED lights.

# This uses the most recent Adafruit library as of 2021
import signal

import adafruit_ws2801
import board
import time

from led_utls.pi_leds import initialize_shutdown_handler

SDI = board.MOSI
CLK = board.SCLK
bright = 1.0

# Configure the count of pixels:
num_pixels = 100

pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=num_pixels, brightness=bright, auto_write=False)

def zipper(pixels, num_pixels, wait):
    r = 50
    g = 50
    b = 50
    color = (255, 255, 255)
    color2 = (255, 255, 255)
    for r in range(10000):
        for i in range(num_pixels):
            pixels.fill((0, 0, 0))
            pixels[i] = color
            pixels[-i] = color2
            if i == num_pixels - i:
                r = r + 1
                if r >= 255:
                    r = 0
                    g = g + 1
                    if g >= 255:
                        b = b + 1
                color = (r & 255, g & 255, b & 255)
                color2 = (b & 255, g & 255, r & 255)
            pixels.show()
            time.sleep(wait)

initialize_shutdown_handler(pixels)

while True:
    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((255, 0, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((255, 0, 0, 0))
    pixels.show()
    time.sleep(0.5)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 255, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 255, 0, 0))
    pixels.show()
    time.sleep(0.3)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 0, 255))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 0, 255, 0))
    pixels.show()
    time.sleep(0.3)

    zipper(pixels, num_pixels, 0.1)
