#!/usr/bin/python

import argparse
import os
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

CLIENT_SECRETS_FILE = 'client_secret.json'
ACCESS_TOKEN_FILE = './access_token.json'

# This OAuth 2.0 access scope allows for read-only access to the authenticated
# user's account, but not other types of account access.
SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Authorization Code: 4/1AWgavdey3PlanGxg-0vFhmAcHwCEBAAEZIWevpd5N5U3d08FaYmBfKYTi7A
# Authorization Code: 4/1AWgavddouFKnIuktRkgjmn3EcFBD6scem0MY1-213I96CbzPuylo0afYaE0

VALID_BROADCAST_STATUSES = ('all', 'active', 'completed', 'upcoming',)

YOUTUBE_PREFIX = "https://youtu.be/"


# Authorize the request and store authorization credentials.
def get_authenticated_service():
    credentials = None

    if os.path.exists(ACCESS_TOKEN_FILE):
        with open(ACCESS_TOKEN_FILE, 'rb') as tokenFile:
            credentials = pickle.load(tokenFile)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # credentials = flow.run_console()
            credentials = flow.run_local_server(port=0)
        with open(ACCESS_TOKEN_FILE, 'wb') as tokenFile:
            pickle.dump(credentials, tokenFile)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def insert_broadcast(youtube):
    print('Create Broadcast')

    list_broadcasts_request = youtube.liveBroadcasts().insert(
        part='id,snippet,status',
        body=dict(
            snippet=dict(
                title='Broadcast title',
                scheduledStartTime='2024-01-30T00:00:00.000Z'
            ),
            status=dict(
                privacyStatus='unlisted',
                selfDeclaredMadeForKids='false'
            )
        )
    )

    insert_broadcast_response = list_broadcasts_request.execute()
    snippet = insert_broadcast_response["snippet"]

    print ("Broadcast '%s' with title '%s' was published at '%s'." % (insert_broadcast_response["id"], snippet["title"], snippet["publishedAt"]))
    print("Youtube URL: %s%s" % (YOUTUBE_PREFIX, insert_broadcast_response["id"]))

    return insert_broadcast_response["id"]


def upload_thumbnail(youtube, video_id, file):
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=file
    ).execute()


# Retrieve a list of broadcasts with the specified status.
def list_broadcasts(youtube, broadcast_status):
    print ('Broadcasts with status "%s":' % broadcast_status)

    list_broadcasts_request = youtube.liveBroadcasts().list(
        broadcastStatus=broadcast_status,
        part='id,snippet',
        maxResults=50
    )

    while list_broadcasts_request:
        list_broadcasts_response = list_broadcasts_request.execute()

        for broadcast in list_broadcasts_response.get('items', []):
            print('%s (%s)' % (broadcast['snippet']['title'], broadcast['id']))

        list_broadcasts_request = youtube.liveBroadcasts().list_next(list_broadcasts_request, list_broadcasts_response)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--broadcast-status',
    #                     help='Broadcast status',
    #                     choices=VALID_BROADCAST_STATUSES,
    #                     default=VALID_BROADCAST_STATUSES[0])
    # args = parser.parse_args()

    youtube = get_authenticated_service()
    try:
        # list_broadcasts(youtube, args.broadcast_status)
        broadcast_id = insert_broadcast(youtube)
        upload_thumbnail(youtube, broadcast_id, 'December_31_2022.png')

    except HttpError as e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))