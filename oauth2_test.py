#!/usr/bin/python

import datetime
import httplib2
import os
import time
import threading

from oauth2client import client
from subprocess import call
from datetime import timedelta, datetime

from gdata.photos.service import *

def oauthLogin():
    # using http://stackoverflow.com/questions/20248555/list-of-spreadsheets-gdata-oauth2/29157967#29157967 (thanks)
    from oauth2client.file import Storage

    filename = os.path.join(os.path.expanduser('~'), ".oauth2_test")
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


def capture(currentTime):
    # TODO: Create album automatically
    ALBUM_ID='6280471381906555329'

    filename = currentTime.strftime("%Y%m%d-%H%M%S") + ".jpg"

    os.system("fswebcam -r 1280x720 --no-banner " + filename)
    gd_client.InsertPhotoSimple(
        '/data/feed/api/user/default/albumid/' + ALBUM_ID,
        'New Photo',
        filename,
        filename,
        content_type='image/jpeg')
    os.system("rm " + filename)


SHOT_PERIOD_IN_SEC = 60

while True:
    now = datetime.now()
    capture(now)
    target = now + timedelta(seconds=SHOT_PERIOD_IN_SEC)
    delta = (target - datetime.now()).total_seconds()
    if delta > 0:
        time.sleep(delta)

