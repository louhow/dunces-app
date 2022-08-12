import json
import os
import re
from slack_sdk import WebClient
import traceback
import random

from dunces.common import CIPHER_SUITE, DAO, SUCCESS, RECOMMENDATION_SERVICE, get_single_match
from dunces.dao.dynamo_dao import DuplicateItemException
from dunces.models.recommendation import UserRecommendation
from dunces.models.slack import SlackUser, SlackRequest, SlackTeam, SlackEventType, SlackChannel
from dunces.models.spotify import SpotifyTrack
from dunces.services.clients.spotify_api import SpotifyApi

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
  track_id = z.group(1) if z and len(z.groups()) >= 1 else None
  return track_id if track_id is not None and 'skip' not in some_str else None


def get_playlist_id(some_str):
  return get_single_match(r'.*https://open.spotify.com/playlist/(\w+).*', some_str)


def send_final_message(req: SlackRequest, message: str):
  slack_team = DAO.get_item(SlackTeam(req.team_id))
  slack_client = WebClient(CIPHER_SUITE.decrypt(slack_team.slack_oauth_token_encrypt))
  slack_client.chat_postMessage(channel=req.channel_id,
                                text=message,
                                thread_ts=req.event_thread_timestamp)
  return SUCCESS


def get_new_recommendation(req):
  new_rec = get_single_match(r'.*recommend ["|“|”](.*)["|“|”]', req.text)
  return UserRecommendation(req.team_id, req.user_id, new_rec) if new_rec is not None else None


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

  # DAO.put_dictionary("audit", "event", event)
  # DAO.put_dictionary("audit", "event_body", event_body)

  try:
    req = SlackRequest.from_event_request(event_body)
    
    if req.get_type() is SlackEventType.APP_MENTION:
      if recommendation_str := get_single_match(r'.*assemble ["|“|”](.*)["|“|”]', req.text):
        rec = RECOMMENDATION_SERVICE.get_recommendation(req.team_id, recommendation_str)
        return send_final_message(req, str(rec))
      
      if user_recommendation := get_new_recommendation(req):
        try:
          rec = RECOMMENDATION_SERVICE.insert_user_recommendation(user_recommendation)
          return send_final_message(req, f'Recommended: {str(rec)}')
        except DuplicateItemException as e:
          return send_final_message(req, f'You already recommended this: {e.get_existing_item()}')
      
      if playlist_id := get_playlist_id(req):
        DAO.put_item(SlackChannel(req.team_id, req.channel_id, playlist_id))
        return send_final_message(req, f"Set playlist {playlist_id} as the default for this channel")

      return send_final_message(req, "Sorry, I don't know what to do with that.")

    if req.text is not None and req.get_type() is SlackEventType.MESSAGE and req.text and not req.event_is_bot_message:
      if track_id := get_track_id(req.text):
        slack_channel = DAO.get_item(SlackChannel(req.team_id, req.channel_id))
        if slack_channel is None:
          return send_final_message(req, 'Cannot add track because playlist is not yet set. @ me with the Spotify playlist URL.')
    
        spotify_track = SpotifyTrack(track_id,
                                     slack_channel.spotify_playlist_id,
                                     req.team_id,
                                     req.user_id,
                                     req.event_timestamp)
        try:
          DAO.insert_item(spotify_track)
        except DuplicateItemException as e:
          # Lambda cold boots may result in slack sending the same event multiple times, so
          # only send a message if this isn't a dupe
          if req.event_timestamp != e.get_existing_item().slack_timestamp:
            return send_duplicate_track_msg(e.get_existing_item(), req)
          return SUCCESS
    
        spotify_api = SpotifyApi(DEFAULT_SLACK_USER, CIPHER_SUITE)
        spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
        return send_final_message(req, f"{random.choice(success_messages)}")
    
    return SUCCESS
  except Exception as e:
    DAO.put_dictionary("audit", "error_event", event)
    DAO.put_dictionary("audit", "error_event_body", event_body)
    print(traceback.format_exc())
  finally:
    return SUCCESS


def send_duplicate_track_msg(existing_track, req):
  if existing_track.slack_user_id is not None:
    dupe_message = f"{random.choice(failure_messages)} This was added on {existing_track.to_date()} - credit to <@{existing_track.slack_user_id}>."
  else:
    dupe_message = f"{random.choice(failure_messages)} This was added sometime before {existing_track.to_date()}."
  return send_final_message(req, dupe_message)
