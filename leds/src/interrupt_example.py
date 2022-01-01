import time

import RPi.GPIO as GPIO

"""
How to handle interrupts on the Raspberry PI
"""

RUN = True


def handle_button_push(channel):
    global RUN
    print("Button push detected ", type(channel), channel)
    GPIO.remove_event_detect(channel)
    RUN = False


GPIO.setmode(GPIO.BCM)
BUTTON_PIN: int = 23
DEBOUNCE_TIME_MS = 300

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Waiting for falling edge on pin 23")
try:
    print("Now do this using a callback")
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button_push, bouncetime=DEBOUNCE_TIME_MS)
    for i in range(100):
        if RUN:
            print("Sleeping for a bit...")
            time.sleep(1)
        else:
            break
except KeyboardInterrupt:
    print("Terminate falling edge detected")
GPIO.cleanup()
