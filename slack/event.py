from cryptography.fernet import Fernet
import json
import os
import re
from slack_sdk import WebClient
import traceback
import random

from service.dao import Dao
from service.models import SpotifyTrack, SlackUser, SlackChannel
from service.spotify_api import SpotifyApi

dao = Dao(os.environ['DYNAMODB_TABLE'])
cipher_suite = Fernet(os.environ['APP_KEY'].encode())

success_messages = [
  "Track added!",
  "Copy that.",
  "Roger that.",
  "10-4, Ghost Rider.",
  "I gotchu mayne",
  "Put it in the books!",
  "Thank you for using BotBot.",
  "Mmm, that's good music."
]

SUCCESS = {
  "statusCode": 200,
  "headers": {
    'Content-Type': 'text/html',
  }
}


def get_track_id(link):
  z = re.match(r"https://open.spotify.com/track/(\w+)", link)
  return z.group(1) if z else None


def handler(event, context):
  data = json.loads(event['body'])
  # TODO verify challenge
  if "challenge" in data:
    return {
      "statusCode": 200,
      "body": data["challenge"],
      "headers": {
        'Content-Type': 'text/html',
      }
    }

  if data['event']['is_bot_user_member'] is False:
    return SUCCESS

  dao.blind_write({**{"PK": "audit", "SK": "event"}, **event})
  dao.blind_write({**{"PK": "audit", "SK": "data"}, **data})

  slack_team_id = data['team_id']
  slack_user_id = data['event']['user']
  slack_user = dao.get_slack_user(SlackUser(slack_team_id, slack_user_id))
  slack_channel = dao.get_slack_channel(SlackChannel(slack_team_id, slack_user_id))
  spotify_api = SpotifyApi(slack_user, slack_channel)

  client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

  try:
    track_id = ''
    for link in data['event']['links']:
      track_id = get_track_id(link['url'])
      if track_id is None:
        continue

      spotify_track = SpotifyTrack(track_id, data['team_id'], data['event']['user'])

      if dao.get_spotify_track(spotify_track):
        client.chat_postMessage(channel=data['event']['channel'],
                                text=f'Looks like this track has already been added')
        return SUCCESS

      dao.insert_spotify_track(spotify_track)
      spotify_api.add_track(spotify_track)
    client.chat_postMessage(channel=data['event']['channel'],
                            text=f"{random.choice(success_messages)}")
    print(event)
  except Exception as e:
    client.chat_postMessage(channel=data['event']['channel'],
                            text='Ruh uh. Something happened @lou.')
    print(traceback.format_exc())
  finally:
    return SUCCESS
