import json
import os
import re
from slack_sdk import WebClient
import traceback
import random

from dunces.common import CIPHER_SUITE, DAO, SUCCESS, RECOMMENDATION_SERVICE, get_single_match
from dunces.helpers.dao import DuplicateItemException
from dunces.models import SpotifyTrack, SlackUser, SlackChannel, SlackRequest, SlackEventType, \
  SlackTeam, UserRecommendation
from dunces.helpers.spotify_api import SpotifyApi

DEFAULT_SLACK_USER = SlackUser(
  'dont',
  'care',
  os.environ['DEFAULT_SPOTIFY_USER_NAME_ENCRYPT'],
  os.environ['DEFAULT_SPOTIFY_USER_REFRESH_TOKEN_ENCRYPT'])

success_messages = [
  "Track added!",
  "Copy that.",
  "Roger that.",
  "10-4, Ghost Rider.",
  "I gotchu mayne",
  "Put it in the books!",
  "Thank you for your patronage.",
  "Mmm, that's good music.",
  "Much obliged.",
  "I dig it."
]

failure_messages = [
  "Looks like someone has good taste.",
  "This track has already been added."
]


def get_track_id(some_str):
  z = re.search(r'.*https://open.spotify.com/track/(\w+).*', some_str)
  return z.group(1) if z and len(z.groups()) >= 1 else None


def get_playlist_id(some_str):
  return get_single_match(r'.*https://open.spotify.com/playlist/(\w+).*', some_str)


def send_message(req: SlackRequest, message: str):
  slack_team = DAO.get_item(SlackTeam(req.team_id))
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
    req = SlackRequest.from_event_request(event_body)

    if req.get_type() is SlackEventType.APP_MENTION:
      recommendation_str = get_single_match(r'.*assemble ["|“|”](.*)["|“|”]', req.text)
      if recommendation_str:
        rec = RECOMMENDATION_SERVICE.get_recommendation(req.team_id, recommendation_str)
        send_message(req, str(rec))
        return SUCCESS

      new_rec = get_single_match(r'.*recommend ["|“|”](.*)["|“|”]', req.text)

      if new_rec:
        user_rec = UserRecommendation(req.team_id, req.user_id, new_rec)
        try:
          rec = RECOMMENDATION_SERVICE.insert_user_recommendation(user_rec)
          send_message(req, f'Recommended: {str(rec)}')
        except DuplicateItemException as e:
          send_message(req, f'You already recommended this: {e.get_existing_item()}')

        return SUCCESS

      playlist_id = get_playlist_id(req.text)
      if playlist_id is not None:
        DAO.put_item(SlackChannel(req.team_id, req.channel_id, playlist_id))
        send_message(req, f"Set playlist {playlist_id} as the default for this channel")
      else:
        send_message(req, "Sorry, I don't know what to do with that.")

      return SUCCESS

    if req.get_type() is not SlackEventType.MESSAGE:
      return SUCCESS

    if req.text is None or req.is_bot_message:
      return SUCCESS

    track_id = get_track_id(req.text)
    if track_id is None:
      return SUCCESS

    if 'skip' in req.text:
      send_message(req, "No worries, I won't add this one.")
      return SUCCESS

    slack_channel = DAO.get_item(SlackChannel(req.team_id, req.channel_id))
    if slack_channel is None:
      send_message(req, 'Cannot add track because playlist is not yet set.')
      return SUCCESS

    spotify_track = SpotifyTrack(track_id, slack_channel.spotify_playlist_id, req.team_id, req.user_id)
    try:
      DAO.insert_item(spotify_track)
    except DuplicateItemException as e:
      send_duplicate_track_msg(e.get_existing_item(), req)
      return SUCCESS

    spotify_api = SpotifyApi(DEFAULT_SLACK_USER, CIPHER_SUITE)
    spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
    send_message(req, f"{random.choice(success_messages)}")
  except Exception as e:
    DAO.put_dictionary("audit", "event", event)
    DAO.put_dictionary("audit", "data", event_body)
    print(traceback.format_exc())
  finally:
    return SUCCESS


def send_duplicate_track_msg(existing_track, req):
  if existing_track.slack_user_id is not None:
    dupe_message = f"{random.choice(failure_messages)} This was added on {existing_track.get_date()} - credit to <@{existing_track.slack_user_id}>."
  else:
    dupe_message = f"{random.choice(failure_messages)} This was added sometime before {existing_track.get_date()}."
  send_message(req, dupe_message)
