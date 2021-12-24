"""
When LEDs start, they display white, when they start showing red, hit the button as fast as possible.
"""
import random
from time import sleep, time

from RPi import GPIO

from led_utls.pi_leds import initialize_leds, show_all_leds, initialize_shutdown_handler, rainbow_cycle

num_pixels = 100

GPIO.setmode(GPIO.BCM)
BUTTON_PIN: int = 23
DEBOUNCE_TIME_MS = 200

led_counter = 0
caught = False
game_on = False
countdown = False
abort = False


def handle_button_push(channel):
    global led_counter
    global caught
    global countdown
    global game_on
    global abort
    if not game_on:
        return
    if countdown:
        print("Button push too early!!!")
        countdown = False
        abort = True
    elif game_on:
        caught = True
        print("Button pushed, with led at position", led_counter)
    else:
        print("Rabbit not running, abort")


def initialize_interrupt(pin: int):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button_push, bouncetime=DEBOUNCE_TIME_MS)


def do_countdown(pixels, start):
    global num_pixels
    global countdown
    countdown = True
    on = (128, 128, 128)
    off = (0, 0, 0)
    pixels.fill(off)
    pixels.show()
    step = num_pixels // start
    for p in range(1, start + 1, 1):
        if not countdown:
            break
        pixels.fill(off)
        for i in range(0, p * step):
            pixels[i] = on
        pixels.show()
        sleep(1.0)
    if countdown:
        # Random delay before start
        delay_time = random.uniform(0, 1) * 5.0
        sleep(delay_time)
    pixels.fill(off)
    pixels.show()
    print('\a', flush=True, end='')
    countdown = False


def do_flasher(pixels, num_pixels):
    rainbow_cycle(pixels, num_pixels=num_pixels, wait=0.001)


def cycle_timer(pixels):
    global num_pixels
    global led_counter
    global caught
    global game_on
    global abort
    waiting_color = (255, 255, 255)
    stopped_color = (255, 0, 0)
    off = (0, 0, 0)
    abort = False
    game_on = True
    do_countdown(pixels, 5)
    if abort:
        print("Too early game aborted")
        game_on = False
        do_flasher(pixels, num_pixels)
        return

    caught = False
    led_counter = 0
    start = time()
    for i in range(num_pixels):
        pixels[i] = waiting_color
        pixels.show()
        led_counter = i
        sleep(0.001)
        if caught:
            elapsed = time() - start
            print(f"Elapsed time {elapsed}, seconds")
            pixels.fill((0, 0, 0))
            for index in range(i):
                pixels[index] = stopped_color
            pixels.show()
            break
        pixels[i] = off
    game_on = False
    if not caught:
        print(f"Too late, button not pushed in time, new game coming up")
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
    while True:
        cycle_timer(pixels)
        for i in range(5, 0, -1):
            print(f"New game in {i} seconds\r", end='')
            sleep(1)
        print(f"New Game Starting!!     ")


if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()
