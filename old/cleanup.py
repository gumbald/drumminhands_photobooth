import RPi.GPIO as GPIO
import time

import Defines as r

GPIO.setmode(GPIO.BCM)

GPIO.setup(r.PIN_LED_PHOTO_RED, GPIO.OUT)
GPIO.setup(r.PIN_LED_PHOTO_YEL, GPIO.OUT)
GPIO.setup(r.PIN_LED_PHOTO_GRE, GPIO.OUT)

GPIO.cleanup()