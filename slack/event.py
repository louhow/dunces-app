import json
import os
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import traceback

from dao.dao import Dao, SpotifyTrack
from spotify.spotify_api import SpotifyApi

dao = Dao(os.environ['DYNAMODB_TABLE'])
spotify_api = SpotifyApi()

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

  try:
    client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
    dao.blind_write({**{"PK": "audit", "SK": "event"}, **event})
    dao.blind_write({**{"PK": "audit", "SK": "data"}, **data})
    for link in data['event']['links']:
      track_id = get_track_id(link)
      dao.insert_spotify_track(
        SpotifyTrack(track_id, data['team_id'], data['event']['user'])
      )
      spotify_api.add_track(track_id)
    client.chat_postMessage(channel='#testing', text=f"hello {track_id}")
    print(event)
  except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["ok"] is False
    assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
    print(f"Got a Slack error: {e.response['error']}")
  except:
    print(traceback.format_exc())
  finally:
    return SUCCESS
