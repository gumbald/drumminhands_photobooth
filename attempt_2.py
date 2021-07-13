"""
Shows basic usage of the Photos v1 API.
Creates a Photos v1 API service and prints the names and ids of the last 10 albums
the user has access to.
"""
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import numpy
from PIL import Image
import requests
import json
import datetime
import cv2
import time

imarray = numpy.random.rand(100,100,3) * 255
im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
im.save('result_image.png')

def takePhoto():
	photoTime = datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")
	photoTitle = "WWW" + photoTime + ".png"
	camera_port = 0
	camera = cv2.VideoCapture(camera_port)
	time.sleep(0.1)  # If you don't wait, the image will be dark
	return_value, image = camera.read()
	cv2.imwrite(photoTitle, image)
	del(camera)
	return photoTitle

def upload(service, file):
	f = open(file, 'rb').read()

	url = 'https://photoslibrary.googleapis.com/v1/uploads'
	headers = {
	    'Authorization': "Bearer " + service._http.request.credentials.access_token,
	    'Content-Type': 'application/octet-stream',
	    'X-Goog-Upload-File-Name': file,
	    'X-Goog-Upload-Protocol': "raw",
	}

	r = requests.post(url, data=f, headers=headers)
	print('\nContent: ' + r.content)
	return r.content

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

	r = requests.post(url, data=bodySerialized, headers=headers)
	print('\nContent: ' + r.content)
	return r.content

def checkAlbum(service, albumName):
	checkUrl = 'https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=true'
	headers = {
	    'Authorization': "Bearer " + service._http.request.credentials.access_token,
	    'Content-Type': 'application/json',
	}

	rCheck = requests.get(checkUrl, headers=headers)
	albums = json.loads(rCheck.content)
#	print(rCheck)
#	return '';
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

	r = requests.post(url, data=bodySerialized, headers=headers)
	print('\nContent: ' + r.content)
	return r.content['id']

# Setup the Photo v1 API
SCOPES = 'https://www.googleapis.com/auth/photoslibrary'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('photoslibrary', 'v1', http=creds.authorize(Http()))

# Call the Photo v1 API
#results = service.albums().list(
#    pageSize=10, fields="nextPageToken,albums(id,title)").execute()
#items = results.get('albums', [])
#if not items:
#    print('No albums found.')
#else:
#    print('Albums:')
#    for item in items:
#        print('{0} ({1})'.format(item['title'].encode('utf8'), item['id']))
#	searchbody = {
#	    "albumId": item['id'],
#	    "pageSize": 10
#	}
#	imagesearch = service.mediaItems().search(body=searchbody).execute()
#	images = imagesearch.get('mediaItems', [])
#	for image in images:
#		print('--> ' + image['filename'])

#newAlbumId = createAlbum(service, 'Photobooth_' + datetime.datetime.now().strftime("%H-%M-%S"))

photoName = takePhoto()
newAlbumId = checkAlbum(service, "Photobooth")
if newAlbumId == '':
	newAlbumId = createAlbum(service, "Photobooth")
print('Album: ' + newAlbumId)

#authenticate user and build service
upload_token = upload(service, photoName)
response = createItem(service, upload_token, newAlbumId)
