import boto3
import os

from dataclasses import fields

from service.models import SlackChannel, SlackUser, SpotifyTrack

DEFAULT_SLACK_USER = SlackUser(
  'dont',
  'care',
  os.environ['DEFAULT_SPOTIFY_USER_NAME_ENCRYPT'],
  os.environ['DEFAULT_SPOTIFY_USER_REFRESH_TOKEN_ENCRYPT'])


def dataclass_from_dict(klass, dikt):
  try:
    fieldtypes = {f.name: f.type for f in fields(klass)}
    return klass(**{f: dataclass_from_dict(fieldtypes[f], dikt[f]) for f in dikt})
  except Exception:
    raise Exception(f'Unable to convert {dikt} to {klass}.')


class Dao(object):
  def __init__(self, table_name):
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
    dict = self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )

    print(klass)
    print(dict)

    return dataclass_from_dict(klass, dict) if dict is not None else None


