import json
import os
import re
from slack_sdk import WebClient
import traceback
import random


from service.dao import Dao
from service.models import SpotifyTrack, SlackUser, SlackChannel, SlackRequest, SlackEventType
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
  z = re.match(r'.*https://open.spotify.com/track/(\w+).*', link)
  return z.group(1) if z and len(z.groups()) >= 1 else None


def handler(event, context):
  event_body = json.loads(event['body'])
  dao.blind_write({**{"PK": "audit", "SK": "event"}, **event})
  dao.blind_write({**{"PK": "audit", "SK": "data"}, **event_body})

  if "challenge" in event_body:
    return {
      "statusCode": 200,
      "body": event_body["challenge"],
      "headers": {
        'Content-Type': 'text/html',
      }
    }

  try:
    req = SlackRequest(event_body)

    if req.type in [SlackEventType.APP_MENTION]:
      return SUCCESS

    if req.type is SlackEventType.MESSAGE and req.is_bot_message:
      return SUCCESS

    if 'skip' in req.text:
      client.chat_postMessage(channel=req.channel_id,
                              text="No worries, I won't add this one.")
      return SUCCESS

    track_id = get_track_id(req.text)
    if track_id is None:
      return SUCCESS

    # Now let's do work!
    spotify_track = SpotifyTrack(track_id, req.team_id, req.user_id)
    existing_track = dao.get_spotify_track(spotify_track)
    if existing_track:
      if spotify_track.slack_user_id is not None:
        dupe_message = f"{random.choice(failure_messages)} This was added on {spotify_track.get_date()} - credit to <@{spotify_track.slack_user_id}>."
      else:
        dupe_message = f"{random.choice(failure_messages)} This was added sometime before {spotify_track.get_date()}."
      client.chat_postMessage(channel=req.channel_id,
                              text=dupe_message)
      return SUCCESS

    dao.insert_spotify_track(spotify_track)
    slack_user = dao.get_slack_user(SlackUser(req.team_id, req.user_id))
    spotify_api = SpotifyApi(slack_user, cipher_suite)
    slack_channel = dao.get_slack_channel(SlackChannel(req.team_id, req.user_id))
    spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
    client.chat_postMessage(channel=req.channel_id,
                            text=f"{random.choice(success_messages)}")
  except Exception as e:
    print(traceback.format_exc())
  finally:
    return SUCCESS
