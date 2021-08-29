from dataclasses import fields

import boto3
import os

from dunces.models import SlackChannel, SlackUser, SpotifyTrack, SlackTeam

DEFAULT_SLACK_USER = SlackUser(
  'dont',
  'care',
  os.environ['DEFAULT_SPOTIFY_USER_NAME_ENCRYPT'],
  os.environ['DEFAULT_SPOTIFY_USER_REFRESH_TOKEN_ENCRYPT'])


def dataclass_from_dict(klass, some_dict):
  try:
    # the database will return values that are re-computed by the dataclasses, so
    # remove those to keep dataclasses from throwing up when initialized
    for f in fields(klass):
      if f.init is False:
        some_dict.pop(f.name, None)

    return klass(**some_dict)
  except Exception:
    raise Exception(f'Unable to convert {some_dict} to {klass}. fieldtypes: {fields(klass)}')


class Dao(object):
  def __init__(self, table_name, public_key=None, private_key=None, endpoint_url=None):
    if endpoint_url is not None:
      client = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    elif public_key is not None and private_key is not None:
      session = boto3.Session(aws_access_key_id=public_key, aws_secret_access_key=private_key)
      client = session.resource('dynamodb')
    else:
      client = boto3.resource('dynamodb')

    self.table = client.Table(table_name)

  def get_spotify_track(self, spotify_track: SpotifyTrack) -> SpotifyTrack:
    return self.__fetch_item(spotify_track, SpotifyTrack)

  def get_slack_user(self, slack_user: SlackUser) -> SlackUser:
    found_user = self.__fetch_item(slack_user, SlackUser)
    return found_user if found_user else DEFAULT_SLACK_USER

  def get_slack_channel(self, slack_channel: SlackChannel) -> SlackChannel:
    return self.__fetch_item(slack_channel, SlackChannel)

  def get_slack_team(self, slack_team: SlackTeam) -> SlackTeam:
    return self.__fetch_item(slack_team, SlackTeam)

  def insert_slack_channel(self, slack_channel: SlackChannel):
    return self.__insert_dataclass(slack_channel)

  def insert_spotify_track(self, spotify_track: SpotifyTrack):
    return self.__insert_dataclass(spotify_track)

  def insert_slack_team(self, slack_team: SlackTeam):
    return self.__insert_dataclass(slack_team)

  def __insert_dataclass(self, some_dataclass):
    self.table.put_item(Item={**some_dataclass.__dict__})
    return some_dataclass

  def blind_write(self, pk, sk, some_dict):
    return self.table.put_item(Item={**{"PK": pk, "SK": sk}, **some_dict})

  def __fetch_item(self, item, klass):
    some_dict = self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )

    item = some_dict.get('Item', None)

    return dataclass_from_dict(klass, item) if item else None
