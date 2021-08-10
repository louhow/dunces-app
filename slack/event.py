import json
import os
import re
from slack_sdk import WebClient
import traceback
import random


from service.dao import Dao
from service.models import SpotifyTrack, SlackUser, SlackChannel, SlackRequest, SlackEventType, \
  SlackTeam
from service.secure import CipherSuite
from service.spotify_api import SpotifyApi

DAO = Dao(os.environ['DYNAMODB_TABLE'])
CIPHER_SUITE = CipherSuite(os.environ['APP_KEY'])

success_messages = [
  "Track added!",
  "Copy that.",
  "Roger that.",
  "10-4, Ghost Rider.",
  "I gotchu mayne",
  "Put it in the books!",
  "Thank you for your patronage.",
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


def get_track_id(some_str):
  z = re.search(r'.*https://open.spotify.com/track/(\w+).*', some_str)
  return z.group(1) if z and len(z.groups()) >= 1 else None


def get_playlist_id(some_str):
  z = re.match(r'.*https://open.spotify.com/playlist/(\w+).*', some_str)
  return z.group(1) if z and len(z.groups()) >= 1 else None


def send_message(req: SlackRequest, message: str):
  slack_team = DAO.get_slack_team(SlackTeam(req.team_id))
  slack_client = WebClient(CIPHER_SUITE.decrypt(slack_team.slack_oauth_token_encrypt))
  slack_client.chat_postMessage(channel=req.channel_id,
                                text=message)


def handler(event, context):
  event_body = json.loads(event['body'])

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

    if req.type is SlackEventType.APP_MENTION:
      playlist_id = get_playlist_id(req.text)
      if playlist_id is not None:
        DAO.insert_slack_channel(SlackChannel(req.team_id, req.channel_id, playlist_id))
        send_message(req, f"Set playlist {playlist_id} as the default for this channel")
      else:
        send_message(req, "Sorry, I don't know what to do with that. I can only set default playlists for now")

      return SUCCESS

    if req.type is not SlackEventType.MESSAGE:
      return SUCCESS

    if req.text is None or req.is_bot_message:
      return SUCCESS

    track_id = get_track_id(req.text)
    if track_id is None:
      return SUCCESS

    if 'skip' in req.text:
      send_message(req, "No worries, I won't add this one.")
      return SUCCESS

    slack_channel = DAO.get_slack_channel(SlackChannel(req.team_id, req.channel_id))
    if slack_channel is None:
      send_message(req, 'Cannot add track because playlist is not yet set.')
      return SUCCESS

    # TODO replace the get/insert pattern with a single insert to save money
    spotify_track = SpotifyTrack(track_id, slack_channel.spotify_playlist_id, req.team_id, req.user_id)
    existing_track = DAO.get_spotify_track(spotify_track)
    if existing_track:
      if spotify_track.slack_user_id is not None:
        dupe_message = f"{random.choice(failure_messages)} This was added on {spotify_track.get_date()} - credit to <@{existing_track.slack_user_id}>."
      else:
        dupe_message = f"{random.choice(failure_messages)} This was added sometime before {spotify_track.get_date()}."
      send_message(req, dupe_message)
      return SUCCESS

    DAO.insert_spotify_track(spotify_track)
    slack_user = DAO.get_slack_user(SlackUser(req.team_id, req.user_id))
    spotify_api = SpotifyApi(slack_user, CIPHER_SUITE)
    spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
    send_message(req, f"{random.choice(success_messages)}")
  except Exception as e:
    DAO.blind_write("audit", "event", event)
    DAO.blind_write("audit", "data", event_body)
    print(traceback.format_exc())
  finally:
    return SUCCESS
