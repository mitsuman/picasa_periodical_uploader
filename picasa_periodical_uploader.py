#!/usr/bin/python

# picasa periodical uploader
#  2016 mitsuman

import argparse
import datetime
import httplib2
import os
import time
import threading

from oauth2client import client
from subprocess import call
from datetime import timedelta, datetime

from gdata.photos.service import *

# Option parser
parser = argparse.ArgumentParser(description='Take a photo and upload picasa(google photo) periodically.')
parser.add_argument('--period', type=int, nargs=1, default=60, help='Shot period in sec')
parser.add_argument('--album-name', default='test', help='Picasa album name')
parser.add_argument('--video-device', default='/dev/video0', help='Video device to take a photo')
args = parser.parse_args()

def oauthLogin():
    # using http://stackoverflow.com/questions/20248555/list-of-spreadsheets-gdata-oauth2/29157967#29157967 (thanks)
    from oauth2client.file import Storage

    filename = os.path.join(os.path.expanduser('~'), ".picasa_periodical_uploader")
    storage = Storage(filename)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json',scope='https://picasaweb.google.com/data/',redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        auth_uri = flow.step1_get_authorize_url()
        print 'Authorization URL: %s' % auth_uri
        auth_code = raw_input('Enter the auth code: ')
        credentials = flow.step2_exchange(auth_code)
        storage.put(credentials)

    # if credentials.access_token_expired:

    return refreshCreds(credentials,0)


def refreshCreds(credentials,sleep):
    global gd_client
    time.sleep(sleep)
    credentials.refresh(httplib2.Http())

    now = datetime.utcnow()
    expires = credentials.token_expiry
    expires_seconds = (expires-now).seconds
    # print ("Expires %s from %s = %s" % (expires,now,expires_seconds) )

    gd_client = gdata.photos.service.PhotosService(email='default',additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token})

    d = threading.Thread(name='refreshCreds', target=refreshCreds, args=(credentials,expires_seconds - 10) )
    d.setDaemon(True)
    d.start()
    return gd_client

gd_client = oauthLogin()


def capture(albumId, currentTime):
    filename = currentTime.strftime("%Y%m%d-%H%M%S") + ".jpg"
    print('Creating Photo: %s ' % filename)

    os.system("fswebcam -q -r 1280x720 --no-banner -d " + args.video_device + " " + filename)
    try:
        gd_client.InsertPhotoSimple(
            '/data/feed/api/user/default/albumid/' + albumId,
            'New Photo',
            filename,
            filename,
            content_type='image/jpeg')
    except GooglePhotosException as gpe:
        print(gpe.message)

    os.system("rm " + filename)


def createAlbum(time, name):
    albumName = time.strftime("%Y%m%d") + name
    print('Creating Album: %s ' % albumName)
    try:
        album = gd_client.InsertAlbum(title=albumName, summary="",access='private')
        return album.gphoto_id.text
    except GooglePhotosException as gpe:
        sys.exit(gpe.message)

# main loop
prevtime = datetime(1970, 1, 1)
albumId = None

while True:
    now = datetime.now()

    if albumId == None or prevtime.date() != now.date():
        albumId = createAlbum(now, args.album_name)

    capture(albumId, now)

    prevtime = now
    target = now + timedelta(seconds=args.period)
    delta = (target - datetime.now()).total_seconds()
    if delta > 0:
        time.sleep(delta)

