#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains reference and master data used elsewhere in the program
'''

# LED GPIO pin mappings
# Used to provide user information on when the photos are being taken
# and for the user to trigger the script by pressing the button controller
# Need to use BOARD numbering convention (not BCM)
PIN_LED_PHOTO_RED = int(4)
PIN_LED_PHOTO_YEL = int(25)
PIN_LED_PHOTO_GRE = int(24)
PIN_SWITCH_IN = int(18)

# Folders on the Pi where the files are saved down
FOLDER_PHOTOS_ORIGINAL = "/home/pi/Wedding/"
FOLDER_PHOTOS_CONVERTED = "/home/pi/Wedding/Converted/"
FOLDER_PHOTOS_MONTAGE = "/home/pi/Wedding/Montages/"
FOLDER_PHOTOS_GIF = "/home/pi/Wedding/GIF/"

# Configuration of each image
# UK passport is 35mm width x 45mm height
PASSPORT_IMAGE_WIDTH = 35
PASSPORT_IMAGE_HEIGHT = 45

# Amount to rotate each image taken
# Handles different orientations of the camera
IMAGE_ROTATE_AMOUNT = 90

# Configuration of the photo montages
MONTAGE_NUMBER_OF_PHOTOS = 4
MONTAGE_PHOTO_WIDTH = PASSPORT_IMAGE_WIDTH * 20
MONTAGE_PHOTO_HEIGHT = PASSPORT_IMAGE_HEIGHT * 20
MONTAGE_MARGINS = [25,25,25,25] # [w, t, r, b]
MONTAGE_PADDING = 25
