import boto3
from models import SlackChannel, SlackUser, SpotifyTrack
import os

DEFAULT_SLACK_USER = SlackUser(
  'dont',
  'care',
  os.environ['DEFAULT_SPOTIFY_USER_NAME_ENCRYPT'],  # TODO
  os.environ['DEFAULT_SPOTIFY_USER_REFRESH_TOKEN_ENCRYPT'])

class Dao(object):
  def __init__(self, table_name):
    client = boto3.resource('dynamodb')
    self.table = client.Table(table_name)

  def get_spotify_track(self, spotify_track: SpotifyTrack) -> SpotifyTrack:
    return self.__fetch_item(spotify_track)

  def get_slack_user(self, slack_user: SlackUser) -> SlackUser:
    found_user = self.__fetch_item(slack_user)
    return found_user if found_user else DEFAULT_SLACK_USER

  def get_slack_channel(self, slack_channel: SlackChannel) -> SlackChannel:
    return self.__fetch_item(slack_channel)

  def insert_spotify_track(self, spotify_track: SpotifyTrack) -> SpotifyTrack:
    return self.table.put_item(Item={**spotify_track.__dict__})

  def blind_write(self, some_dict):
    self.table.put_item(Item={**some_dict})

  def __fetch_item(self, item):
    return self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )
