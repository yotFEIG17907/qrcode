import time
from typing import Tuple, Any, List

import adafruit_ws2801
import board

from led_messages.led_commands import FillAll, Zipper, SetPixels


class LEDStrand(object):
    """
    Controlling a strand of WS2801 LEDs
    """

    def __init__(self, n: int, brightness: float = 1.0):
        """
        Connect to the driver for the LEDs
        :param n: The number of LEDs in the strand
        :param brightness: A brightness factor to multiply the color values
        """
        # Set up for the LEDs. This is for the Raspberry PI, this depends on the strand's
        # data and clock being connected to these pins
        SDI = board.MOSI
        CLK = board.SCLK
        # Auto-write is false which means that new values written to the strand do not
        # take effect until "pixels.show" is called
        self.pixels = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=n, brightness=brightness, auto_write=False)
        self.num_pixels = n

    def cleanup(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def fill(self, color: Tuple[int, int, int]):
        self.pixels.fill(color=color)
        self.pixels.show()

    def zipper(self, wait: float):
        r = 50
        g = 50
        b = 50
        color = (255, 255, 255)
        color2 = (255, 255, 255)
        for r in range(10000):
            for i in range(self.num_pixels):
                self.pixels.fill((0, 0, 0))
                self.pixels[i] = color
                self.pixels[-i] = color2
                if i == self.num_pixels - i:
                    r = r + 1
                    if r >= 255:
                        r = 0
                        g = g + 1
                        if g >= 255:
                            b = b + 1
                    color = (r & 255, g & 255, b & 255)
                    color2 = (b & 255, g & 255, r & 255)
                self.pixels.show()
                time.sleep(wait)

    def set_pixels(self, values: List[Tuple[int, int, int]]) -> None:
        """
        Set all the pixel values then show
        :param values: A list of tuples to set each LED
        :return: Nothing
        """
        for idx, i in enumerate(values):
            self.pixels[idx] = i
        self.pixels.show()


    def execute(self, cmd: Any):
        if isinstance(cmd, FillAll):
            self.fill(cmd.payload)
        elif isinstance(cmd, Zipper):
            self.zipper(wait=cmd.payload)
        elif isinstance(cmd, SetPixels):
            self.set_pixels(cmd.payload)
        else:
            print("Unsupported cmd", type(cmd))
