import board
import time
import adafruit_ws2801

SDI = board.MOSI
CLK = board.SCLK
n_leds = 100
bright = 1.0

print("Create the leds gateway");
leds = adafruit_ws2801.WS2801(clock=CLK, data=SDI, n=n_leds, brightness=bright, auto_write=True)
leds.fill((0x80, 0x40, 0))
print("Leds filled")
wait_seconds = 5.0
print(f"Wait a bit {wait_seconds} seconds")
time.sleep(wait_seconds)
leds.fill((0, 0, 0))
print("All done...")
