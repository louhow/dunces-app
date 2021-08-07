from dataclasses import fields

import boto3
import os

from service.models import SlackChannel, SlackUser, SpotifyTrack

DEFAULT_SLACK_USER = SlackUser(
  'dont',
  'care',
  os.environ['DEFAULT_SPOTIFY_USER_NAME_ENCRYPT'],
  os.environ['DEFAULT_SPOTIFY_USER_REFRESH_TOKEN_ENCRYPT'])


def dataclass_from_dict(klass, dikt):
  try:
    # the database will return values that are re-computed by the dataclasses, so
    # remove those to keep dataclasses from throwing up when initialized
    for f in fields(klass):
      if f.init is False:
        dikt.pop(f.name, None)

    return klass(**dikt)
  except Exception:
    raise Exception(f'Unable to convert {dikt} to {klass}. fieldtypes: {fields(klass)}')


class Dao(object):
  def __init__(self, table_name, public_key=None, private_key=None):
    if public_key is not None and private_key is not None:
      session = boto3.Session(aws_access_key_id=public_key, aws_secret_access_key=private_key)
      client = session.resource('dynamodb')
    else:
      client = boto3.resource('dynamodb')

    self.table = client.Table(table_name)

  def get_spotify_track(self, spotify_track: SpotifyTrack) -> SpotifyTrack:
    return self.__fetch_item(SpotifyTrack, spotify_track)

  def get_slack_user(self, slack_user: SlackUser) -> SlackUser:
    found_user = self.__fetch_item(SlackUser, slack_user)
    return found_user if found_user else DEFAULT_SLACK_USER

  def get_slack_channel(self, slack_channel: SlackChannel):
    found_slack_channel = self.__fetch_item(SlackChannel, slack_channel)
    return found_slack_channel if found_slack_channel else SlackChannel(
      slack_channel.slack_team_id,
      slack_channel.slack_channel_id,
      os.environ['SPOTIFY_THREAD_PLAYLIST_ID']
    )

  def insert_spotify_track(self, spotify_track: SpotifyTrack):
    self.table.put_item(Item={**spotify_track.__dict__})

  def blind_write(self, some_dict):
    self.table.put_item(Item={**some_dict})

  def __fetch_item(self, klass, item):
    dikt = self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )

    item = dikt.get('Item', None)

    return dataclass_from_dict(klass, item) if item else None
