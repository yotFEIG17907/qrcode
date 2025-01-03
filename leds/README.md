# Overview

This package is all about controlling a strand of WS2801 LEDs using Python script running on Raspberry PI. And it also
has many sound-to-light scripts which demonstrate how to get input sound from a microphone, how to run FFTs on that
sound stream and then display the Fourier Spectrum on the LED Strands. And there is a Reaction Timer script; this
script demonstrates how to handle and interrupt in Python. There are a bunch of scripts which represent investigations
many of which are dead ends.

Python is not the swiftest but it works surprisingly well.

## The FFT sound-to-light Scripts

Most of these generate the FFTs and also control the LEDs directly through the GPIO. A few of the FFT scripts control
the LEDs indirectly by sending messages to MQTT; this is a nice split between the FFT code and the display and offloads
control of the LEDs to another RaspberryPI 

## led_mqtt_client

This script turns the LEDs on and off based on messages received via MQTT. It should be executed on a Raspberry PI whose
GPIO pins are connected to the LED Strand.

## led_mqtt_test_driver

This generates test patterns and publishes them to MQTT it is for testing that LED_MQTT_CLIENT is working.





