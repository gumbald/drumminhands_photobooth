#!/usr/bin/env python

running_on_pi = False
upload_ftp = False
upload_gphotos = False
run_fullscreen = False

photos_filmstrip = False
photos_single = True
photos_gif = False

# Folders on the Pi where the files are saved down
FOLDER_PHOTOS_ORIGINAL = "../Photos/Wedding/"
FOLDER_PHOTOS_CONVERTED = "../Photos/Wedding/Converted/"
FOLDER_PHOTOS_MONTAGE = "../Photos/Wedding/Montages/"
FOLDER_PHOTOS_GIF = "../Photos/Wedding/GIF/"
FOLDER_PHOTOS_SHRUNK = "../Photos/Wedding/Shrunk/"

import os
import glob
import time
from time import sleep
import argparse

if running_on_pi:
    import RPi.GPIO as GPIO
    from signal import alarm, signal, SIGALRM, SIGKILL

import atexit
import pygame
import subprocess
import logging
from PIL import Image
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import config # this is the config python file config.py
import definitions as r
#import twitter
import ftplib
from os import system
import cv2
import time
from time import gmtime, strftime, sleep
from random import randint
import json
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import numpy
from google.auth.transport import requests as g
import requests
import datetime

########################
### Variables Config ###
########################
led_pin = 19 # LED 
btn_pin = 5 # pin for the start button

total_pics = 4 # number of pics to be taken
capture_delay = 1 # delay between pics
prep_delay = 2 # number of seconds at step 1 as users prep to have photo taken
gif_delay = 100 # How much time between frames in the animated gif
restart_delay = 4 # how long to display finished message before beginning a new session
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

if running_on_pi:
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led_pin,GPIO.OUT) # LED
    GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.output(led_pin,False) #for some reason the pin turns on at the beginning of the program. Why?

# initialize pygame
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False) #hide the mouse cursor
if run_fullscreen:
    pygame.display.toggle_fullscreen()

#################
### Functions ###
#################
def upload(service, file):
	f = open(file, 'rb').read()

	url = 'https://photoslibrary.googleapis.com/v1/uploads'
	headers = {
	    'Authorization': "Bearer " + service._http.request.credentials.access_token,
	    'Content-Type': 'application/octet-stream',
	    'X-Goog-Upload-File-Name': file,
	    'X-Goog-Upload-Protocol': "raw",
	}

	res = requests.post(url, data=f, headers=headers)
	print('\nContent: ' + res.content)
	return res.content

def createItem(service, upload_token, albumId):
	url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'

	body = {
	    'newMediaItems' : [
		{
		    "description": "",
		    "simpleMediaItem": {
		        "uploadToken": upload_token
		    }
		}
	    ]
	}

	if albumId is not None:
	    body['albumId'] = albumId

	bodySerialized = json.dumps(body)
	headers = {
	    'Authorization': "Bearer " + service._http.request.credentials.access_token,
	    'Content-Type': 'application/json',
	}

	print('\nBody: ' + bodySerialized)

	res = requests.post(url, data=bodySerialized, headers=headers)
	print('\nContent: ' + res.content)
	return res.content

def checkAlbum(service, albumName):
    print(service._http.request.credentials.access_token)
    checkUrl = 'https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=true'
    headers = {
        'Authorization': "Bearer " + service._http.request.credentials.access_token,
        'Content-Type': 'application/json',
    }
    
    rCheck = requests.get(checkUrl, headers=headers)
    print(rCheck.status_code)
    if rCheck.status_code == 401:
        print('Need to refresh...')
        request = g.Request()
        print(request)
        print(creds)
        creds.refresh(Http())
        print(creds['access_token'])
    albums = json.loads(rCheck.content)
#	print(rCheck)
#	return ''
    
    print(albums)
    
    if len(albums['albums']) == 1:
        return albums['albums'][0]['id']
    else:
        return ''

def createAlbum(service, albumName):
	url = 'https://photoslibrary.googleapis.com/v1/albums'

	body = {
	    'album' : {
		    "title": albumName
	    }
	}

	bodySerialized = json.dumps(body)
	headers = {
	    'Authorization': "Bearer " + service._http.request.credentials.access_token,
	    'Content-Type': 'application/json',
	}

	print('\nBody: ' + bodySerialized)

	res = requests.post(url, data=bodySerialized, headers=headers)
	print('\nContent: ' + res.content)
	return res.content['id']

def actuate_camera_shutter(img_size):
    '''
    Actuates the camera and downloads the image onto the Raspberry Pi
    :return: the filepath of the photo taken
    '''

    image_name = "photobooth_" + strftime("%Y-%m-%d_%H%M%S", gmtime()) + ".jpg"
    image_filepath = FOLDER_PHOTOS_ORIGINAL + image_name
    gpout = ""

    try:
        gpout = subprocess.check_output("gphoto2 --set-config /main/imgsettings/imagesize=" + str(img_size), stderr=subprocess.STDOUT, shell=True)
        gpout = subprocess.check_output("gphoto2 --capture-image-and-download --keep --filename " + image_filepath, stderr=subprocess.STDOUT, shell=True)

        # CalledProcessError is raised when the camera is turned off (or battery dies?)

        if "ERROR" in gpout:
            print(gpout)
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
    if running_on_pi:
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

def takePhoto():
    photoTitle = FOLDER_PHOTOS_ORIGINAL + "photobooth_" + strftime("%Y-%m-%d_%H%M%S", gmtime()) + ".jpg"
    camera_port = 0
    camera = cv2.VideoCapture(camera_port)
    time.sleep(0.1)  # If you don't wait, the image will be dark
    return_value, image = camera.read()
    cv2.imwrite(photoTitle, image)
    del(camera)
    return photoTitle

# define the photo taking function for when the big button is pressed 
def start_photobooth(): 

    input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.

    try:
        print("Get Ready")
        if running_on_pi:
            GPIO.output(led_pin,False)
        
        take_extra_photos = False
        #random_decider = randint(0,10)
        #pose_gap = randint(1,3)
        random_decider = 1
        pose_gap = 1
        
        if random_decider == 0:
                take_extra_photos = True
        
        show_image(real_path + "/images/pose3.png")
        sleep(pose_gap)
        
        show_image(real_path + "/images/pose2.png")
        sleep(pose_gap)
                
        show_image(real_path + "/images/pose1.png")
        sleep(pose_gap)

        show_image(real_path + "/images/instructions.png")
        sleep(pose_gap)
        
        filename = ""
        
        now = time.strftime("%Y-%m-%d_%H%M%S") #get the current date and time for the start of the filename
        print(now)
        
        if running_on_pi:
            filename_gif = actuate_camera_shutter(1)
        else:
            filename_gif = takePhoto()

        print(filename_gif)
        
        if running_on_pi:
            system('convert ' + filename_gif + ' -resize 50% ' + FOLDER_PHOTOS_SHRUNK + now + ".jpg")
        else:
            system('convert ' + filename_gif + ' ' + FOLDER_PHOTOS_SHRUNK + now  + ".jpg")
        
        filename = FOLDER_PHOTOS_GIF + now + '.gif'

        # clear the screen
        #clear_screen()
        #show_image(real_path + "/snap1.png")
        
        if take_extra_photos:
            print("Entering photo loop")
            for x in range(0, 3):
                    if running_on_pi:
                        filename_gif = actuate_camera_shutter(1)
                    else:
                        filename_gif = takePhoto()
                    if x == 0:
                            show_image(real_path + "/images/snap2.png")
                    elif x == 1:
                            show_image(real_path + "/images/snap3.png")
                    #elif x == 2:
                    #        show_image(real_path + "/gif3.png")
                    #print filename_gif
                    system('convert ' + filename_gif + ' -resize 50% ' + FOLDER_PHOTOS_SHRUNK + now + "_" + str(x) + ".jpg")
                    #os.rename(r.FOLDER_PHOTOS_SHRUNK + filename_gif, r.FOLDER_PHOTOS_SHRUNK)
            filename = FOLDER_PHOTOS_GIF + now + '.gif'
        #else:
        #        filename = actuate_camera_shutter(0)
    
        ########################### Begin Step 3 #################################
        
        input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
        
        show_image(real_path + "/images/processing.png")
        sleep(prep_delay)
        
        #if take_extra_photos:
        #        show_image(real_path + "/animating.png")
            # MAKE COLLAGE HERE
        if photos_filmstrip:
            strip = Image.new('RGB', (1300, 2460), (255,255,255))
            y = 126
            filename = "FILMSTRIP_" + now + ".jpg"
            for filename_add in glob.glob(FOLDER_PHOTOS_SHRUNK + now + '_*.jpg'):
                jpgfile = Image.open(filename_add)
                strip.paste(jpgfile, (86, y))
                strip.save(filename)
                y = y + 778
                #system('convert -delay 25 -loop 0 ' + r.FOLDER_PHOTOS_SHRUNK + now + '_*.jpg ' + r.FOLDER_PHOTOS_GIF + now + '.gif')
        #else:
        show_image(filename_gif)
        sleep(prep_delay)

        print("Uploading")
        show_image(real_path + "/images/uploading.png")
        
        #status = api.PostUpdate('#nottheonlyjbinthevillage',media=filename)
        if upload_ftp:
            session = ftplib.FTP(config.ftp_server,config.ftp_username,config.ftp_password)
            file = open(filename,'rb')                  # file to send
            #session.cwd('images')
            session.storbinary('STOR ' + now + '.jpg', file)     # send the file
            file.close()                                    # close file and FTP
            session.quit()
            
        if upload_gphotos:
            print("Upload to Google Photos!")
            photoName = filename_gif
            print(photoName)
            newAlbumId = checkAlbum(service, "Watson Woodland Wedding")
            if newAlbumId == '':
                newAlbumId = createAlbum(service, "Watson Woodland Wedding")
            print('Album: ' + newAlbumId)
            
            #authenticate user and build service
            upload_token = upload(service, photoName)
            response = createItem(service, upload_token, newAlbumId)
        
        time.sleep(restart_delay)
    
        ########################### Begin Step 4 #################################
        
        input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
                
        print("Done")
        
        #show_image(real_path + "/finished.png")
        
        #time.sleep(restart_delay)
        
        show_image(real_path + "/images/intro.png")

    except Exception as e: 
        print(e)
        show_image(real_path + "/images/again.png")
        time.sleep(5)

####################
### Main Program ###
####################

print("Photo booth app running..." )

#api = twitter.Api(consumer_key=config.consumer_key,
#                      consumer_secret=config.consumer_secret,
#                      access_token_key=config.access_token_key,
#                      access_token_secret=config.access_token_secret)
                      
#print(api.VerifyCredentials())

show_image(real_path + "/images/intro.png")

if upload_gphotos:
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary'
    store = file.Storage('../credentials.json')
    creds = store.get()
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--logging_level', default='ERROR')
    parser.add_argument('--noauth_local_webserver', action='store_true',
                default=True, help='Do not run a local web server.')
    args = parser.parse_args([])
    print(creds)
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('../client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, args)
    service = build('photoslibrary', 'v1', http=creds.authorize(Http()))
    if upload_gphotos:
        newAlbumId = checkAlbum(service, "Photobooth")
    print(service)
    
while True:
    show_image(real_path + "/images/intro.png")
    if running_on_pi:
        GPIO.output(led_pin,True) #turn on the light showing users they can push the button
        input_state = GPIO.input(btn_pin)
        if input_state == False:
            start_photobooth()
    else:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    start_photobooth()
                if event.key == pygame.K_e:
                    quit()
