"""
When LEDs start, they display white, when they start showing red, hit the button as fast as possible.
"""
from time import sleep, time

from RPi import GPIO

from leds.src.led_utls.pi_leds import initialize_leds, show_all_leds, initialize_shutdown_handler

num_pixels = 100

GPIO.setmode(GPIO.BCM)
BUTTON_PIN: int = 23
DEBOUNCE_TIME_MS = 200

led_counter = 0
stop = False

def handle_button_push(channel):
    global led_counter
    global stop
    stop = True
    print("Button pushed, led at", led_counter)


def initialize_interrupt(pin: int):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button_push, bouncetime=DEBOUNCE_TIME_MS)


def countdown(pixels, start):
    toggler = True
    for p in range(start, 0, -1):
        if toggler:
            pixels.fill((255, 255, 255))
        else:
            pixels.fill((0, 0, 0))
        toggler = not toggler
        pixels.show()
        sleep(1.0)
    pixels.fill((0, 0, 0))
    pixels.show()


def cycle_timer(pixels):
    global num_pixels
    global led_counter
    global stop
    waiting_color = (255, 255, 255)
    stopped_color = (255, 0, 0)
    off = (0, 0, 0)
    countdown(pixels, 5)
    start = time()
    for i in range(num_pixels):
        pixels[i] = waiting_color
        pixels.show()
        led_counter = i
        sleep(0.001)
        if stop:
            elapsed = time() - start
            print(f"Elapsed time {elapsed}, seconds, expected {100 * 1} mS")
            for index in range(i):
                pixels[i] = stopped_color
            pixels.show()
            sleep(10)
            break
        pixels[i] = off
    pixels.fill((0, 0, 0))
    pixels.show()


def main():
    global num_pixels
    pixels = initialize_leds(n=num_pixels, brightness=1.0)
    print("LEDs initialized")
    initialize_shutdown_handler(pixels)
    show_all_leds(pixels)
    sleep(3)
    initialize_interrupt(BUTTON_PIN)
    cycle_timer(pixels)


if __name__ == "__main__":
    try:
      main()
    finally:
      GPIO.cleanup()
