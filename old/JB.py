#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import RPi.GPIO as GPIO
#from PIL import Image
import subprocess
from time import gmtime, strftime, sleep
import logging
import RPi.GPIO as GPIO

#from ImageManipulation import convert_photo_to_monochrome, crop_image_to_centre, create_image_montage, rotate_image

import InOut
import Defines as r

# Set up the various GPIO pins on the Raspberry Pi
# Broad numbering convention for naming the pins
GPIO.setmode(GPIO.BCM)

# Output LEDs used for the photos taken
GPIO.setup(r.PIN_LED_PHOTO_RED, GPIO.OUT)
GPIO.setup(r.PIN_LED_PHOTO_YEL, GPIO.OUT)
GPIO.setup(r.PIN_LED_PHOTO_GRE, GPIO.OUT)

# Indicate to the user that the script has started sucessfully by flashing all LEDs
InOut.script_event_indicator()

try: # Wrap in try loop in order to include KeyboardInterupt exception catch

    while True:    # Constantly cycles throuch script, waiting for the trigger event

        # Activate the "ready" LED
        GPIO.output(r.PIN_LED_PHOTO_GRE,True)

        sleep(0.2) #Used to prevent 'switch bounce'

except KeyboardInterrupt:
    print "User ended process with KeyboardInterupt"
    #InOut.turn_off_all_leds([r.PIN_LED_PHOTO_RED, r.PIN_LED_PHOTO_YEL, r.PIN_LED_PHOTO_GRE])
    logging.debug("Process interupted by keyboard interupt")
    GPIO.cleanup()

