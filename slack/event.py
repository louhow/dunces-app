import json
import os
import re
from slack_sdk import WebClient
import traceback
import random


from service.dao import Dao
from service.models import SpotifyTrack, SlackUser, SlackChannel
from service.secure import CipherSuite
from service.spotify_api import SpotifyApi

dao = Dao(os.environ['DYNAMODB_TABLE'])
cipher_suite = CipherSuite(os.environ['APP_KEY'])
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

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

failure_messages = [
  "Looks like someone has good taste.",
  "This track has already been added."
]

SUCCESS = {
  "statusCode": 200,
  "headers": {
    'Content-Type': 'text/html',
  }
}


def get_track_id(link):
  z = re.match(r'https://open.spotify.com/track/(\w+)', link)
  return z.group(1) if z and len(z.groups()) >= 1 else None


def handler(event, context):
  data = json.loads(event['body'])

  if "challenge" in data:
    return {
      "statusCode": 200,
      "body": data["challenge"],
      "headers": {
        'Content-Type': 'text/html',
      }
    }

  if data['event'].get('is_bot_user_member', False) is False:
    return SUCCESS

  dao.blind_write({**{"PK": "audit", "SK": "event"}, **event})
  dao.blind_write({**{"PK": "audit", "SK": "data"}, **data})

  slack_channel_id = data['event']['channel']
  try:
    slack_team_id = data['team_id']
    slack_user_id = data['event']['user']
    slack_user = dao.get_slack_user(SlackUser(slack_team_id, slack_user_id))
    slack_channel = dao.get_slack_channel(SlackChannel(slack_team_id, slack_user_id))
    spotify_api = SpotifyApi(slack_user, cipher_suite)

    for link in data['event']['links']:
      track_id = get_track_id(link['url'])
      if track_id is None:
        continue

      spotify_track = SpotifyTrack(track_id, data['team_id'], data['event']['user'])
      existing_track = dao.get_spotify_track(spotify_track)
      if existing_track:
        if spotify_track.slack_user_id is not None:
          dupe_message = f"{random.choice(failure_messages)} This was added on {spotify_track.get_date()}, credit to <@{spotify_track.slack_user_id}>."
        else:
          dupe_message = f"{random.choice(failure_messages)} This was added sometime before {spotify_track.get_date()}."
        client.chat_postMessage(channel=slack_channel_id,
                                text=dupe_message)
        return SUCCESS

      dao.insert_spotify_track(spotify_track)
      spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
    client.chat_postMessage(channel=slack_channel_id,
                            text=f"{random.choice(success_messages)}")
    print(event)
  except Exception as e:
    client.chat_postMessage(channel=slack_channel_id,
                            text=traceback.format_exc())
  finally:
    return SUCCESS
