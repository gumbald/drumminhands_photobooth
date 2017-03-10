#!/usr/bin/env python
# created by chris@drumminhands.com
# see instructions at http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/

import os
import glob
import time
import traceback
from time import sleep
import RPi.GPIO as GPIO
import picamera # http://picamera.readthedocs.org/en/release-1.4/install2.html
import atexit
import sys
import socket
import pygame
import subprocess
import logging
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
#import pytumblr # https://github.com/tumblr/pytumblr
import config # this is the config python file config.py
from signal import alarm, signal, SIGALRM, SIGKILL
from time import gmtime, strftime, sleep
from random import randint
import definitions as r
import twitter
import imageio

########################
### Variables Config ###
########################
led_pin = 7 # LED 
btn_pin = 18 # pin for the start button

total_pics = 4 # number of pics to be taken
capture_delay = 1 # delay between pics
prep_delay = 2 # number of seconds at step 1 as users prep to have photo taken
gif_delay = 100 # How much time between frames in the animated gif
restart_delay = 10 # how long to display finished message before beginning a new session
test_server = 'www.google.com'

#############################
### Variables that Change ###
#############################
# Do not change these variables, as the code will change it anyway
transform_x = config.monitor_w # how wide to scale the jpg when replaying
transform_y = config.monitor_h # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 2 # how many times to show each photo on-screen after taking

####################
### Other Config ###
####################
real_path = os.path.dirname(os.path.realpath(__file__))

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin,GPIO.OUT) # LED
GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(led_pin,False) #for some reason the pin turns on at the beginning of the program. Why?

# initialize pygame
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False) #hide the mouse cursor
pygame.display.toggle_fullscreen()

#################
### Functions ###
#################

def actuate_camera_shutter(img_size):
    '''
    Actuates the camera and downloads the image onto the Raspberry Pi
    :return: the filepath of the photo taken
    '''

    image_name = "photobooth_" + strftime("%Y-%m-%d_%H%M%S", gmtime()) + ".jpg"
    image_filepath = r.FOLDER_PHOTOS_ORIGINAL + image_name
    gpout = ""

    try:
	gpout = subprocess.check_output("gphoto2 --set-config /main/imgsettings/imagesize=" + img_size, stderr=subprocess.STDOUT, shell=True)
        gpout = subprocess.check_output("gphoto2 --capture-image-and-download --keep --filename " + image_filepath, stderr=subprocess.STDOUT, shell=True)

        # CalledProcessError is raised when the camera is turned off (or battery dies?)

        if "ERROR" in gpout:
            print gpout
            logging.error(gpout)
            raise IOError("Not able to take photo as the command failed for photo " + image_filepath)

    except subprocess.CalledProcessError as e:
        logging.error("Unable to take photo, likely due to camera not responding - check batteries")
        logging.error(e)
        raise

    except Exception as e:
        logging.error("Unable to take photo as the command failed for photo " + image_filepath)
        logging.error(e)
        raise
    else:
        return image_filepath

# clean up running programs as needed when main program exits
def cleanup():
  print('Ended abruptly')
  pygame.quit()
  GPIO.cleanup()
atexit.register(cleanup)

# A function to handle keyboard/mouse/device input events    
def input(events):
    for event in events:  # Hit the ESC key to quit the slideshow.
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key == K_ESCAPE)):
            pygame.quit()

	
# set variables to properly display the image on screen at right ratio
def set_dimensions(img_w, img_h):
	# Note this only works when in booting in desktop mode. 
	# When running in terminal, the size is not correct (it displays small). Why?

    # connect to global vars
    global transform_y, transform_x, offset_y, offset_x

    # based on output screen resolution, calculate how to display
    ratio_h = (config.monitor_w * img_h) / img_w 

    if (ratio_h < config.monitor_h):
        #Use horizontal black bars
        #print "horizontal black bars"
        transform_y = ratio_h
        transform_x = config.monitor_w
        offset_y = (config.monitor_h - ratio_h) / 2
        offset_x = 0
    elif (ratio_h > config.monitor_h):
        #Use vertical black bars
        #print "vertical black bars"
        transform_x = (config.monitor_h * img_w) / img_h
        transform_y = config.monitor_h
        offset_x = (config.monitor_w - transform_x) / 2
        offset_y = 0
    else:
        #No need for black bars as photo ratio equals screen ratio
        #print "no black bars"
        transform_x = config.monitor_w
        transform_y = config.monitor_h
        offset_y = offset_x = 0
# display one image on screen
def show_image(image_path):

	# clear the screen
	screen.fill( (0,0,0) )

	# load the image
	img = pygame.image.load(image_path)
	img = img.convert() 

	# set pixel dimensions based on image
	set_dimensions(img.get_width(), img.get_height())

	# rescale the image to fit the current display
	img = pygame.transform.scale(img, (transform_x,transform_y))
	screen.blit(img,(offset_x,offset_y))
	pygame.display.flip()	
	
# display a blank screen
def clear_screen():
	screen.fill( (0,0,0) )
	pygame.display.flip()

# display a group of images
def display_pics(jpg_group):
    for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, total_pics+1): #show each pic
			show_image(config.file_path + jpg_group + "-0" + str(i) + ".jpg")
			time.sleep(replay_delay) # pause 
				
# define the photo taking function for when the big button is pressed 
def start_photobooth(): 

	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.

	################################# Begin Step 1 #################################
	
	print "Get Ready"
	#GPIO.output(led_pin,False);
	show_image(real_path + "/instructions.png")
	sleep(prep_delay)
	
	take_extra_photos = False
	random_decider = randint(0,1)
	pose_gap = randint(0,2)
	
	if random_decider == 0:
		take_extra_photos = True
		pose_gap=0.1
	
	show_image(real_path + "/pose3.png")
	sleep(pose_gap)
	
	if take_extra_photos:
		filename3 = actuate_camera_shutter(2)
	
	show_image(real_path + "/pose2.png")
	sleep(pose_gap)
	
	if take_extra_photos:
		filename2 = actuate_camera_shutter(2)
		
	show_image(real_path + "/pose1.png")
	sleep(pose_gap)
	
	if take_extra_photos:
		filename1 = actuate_camera_shutter(2)
	
	now = time.strftime("%Y-%m-%d-%H-%M-%S") #get the current date and time for the start of the filename
	print now
	
	extra_files = [ filename1, filename2, filename3 ]
	images = []

	if take_extra_photos:
		for filename in extra_files:
    			images.append(imageio.imread(filename))
		imageio.mimwrite(r.FOLDER_PHOTOS_GIF + now + ".gif",images)
	
	# clear the screen
	clear_screen()
		
	################################# Begin Step 2 #################################
	
	print "Taking pics"
  
	filename = actuate_camera_shutter(0);
  
	########################### Begin Step 3 #################################
	
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	
	show_image(real_path + "/processing.png")
	
	sleep(prep_delay)
	
	show_image(filename)
	
	sleep(prep_delay)
	
	show_image(real_path + "/uploading.png")
	
	#status = api.PostUpdate('#nottheonlyjbinthevillage',media=filename)
	
	time.sleep(restart_delay)
    
	########################### Begin Step 4 #################################
	
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
		
	print "Done"
	
	show_image(real_path + "/finished.png")
	
	time.sleep(restart_delay)
	
	show_image(real_path + "/intro.png");

####################
### Main Program ###
####################

print "Photo booth app running..." 

api = twitter.Api(consumer_key=config.consumer_key,
                      consumer_secret=config.consumer_secret,
                      access_token_key=config.access_token_key,
                      access_token_secret=config.access_token_secret)
                      
print(api.VerifyCredentials())

show_image(real_path + "/intro.png");

while True:
	#GPIO.output(led_pin,True); #turn on the light showing users they can push the button
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_j:
					start_photobooth()
	#GPIO.wait_for_edge(btn_pin, GPIO.FALLING)
	#time.sleep(config.debounce) #debounce
	#start_photobooth()
