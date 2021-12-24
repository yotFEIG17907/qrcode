# Simple demo of of the WS2801/SPI-like addressable RGB LED lights.

# This uses the most recent Adafruit library as of 2021

import time

import adafruit_ws2801
import board

SDI = board.MOSI
CLK = board.SCLK
bright = 1.0

# Configure the count of pixels:
num_pixels = 100

pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=num_pixels, brightness=bright, auto_write=False)




def zipper(pixels, num_pixesl, wait):
    r = 0
    g = 0
    b = 0
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


while True:
    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((255, 0, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((255, 0, 0, 0))
    pixels.show()
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 255, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 255, 0, 0))
    pixels.show()
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 0, 255))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 0, 255, 0))
    pixels.show()
    time.sleep(1)

    #rainbow_cycle(pixels, num_pixels, 0.001)  # rainbow cycle with 1ms delay per step
    zipper(pixels, num_pixels, 0.01)
