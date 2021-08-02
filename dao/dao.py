import boto3
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os


@dataclass
class SpotifyTrack:
  external_track_id: str
  slack_team_id: str
  slack_user_id: str
  slack_team_user_id: str = field(init=False)
  PK: str = field(init=False)
  SK: str = field(init=False)
  create_time: str = datetime.now(timezone.utc).isoformat()
  external_playlist_id: str = os.environ['SPOTIFY_THREAD_PLAYLIST_ID']

  def __post_init__(self):
    self.PK = "PLAYLIST#" + self.external_playlist_id
    self.SK = "TRACK#" + self.external_track_id
    self.slack_team_user_id = self.slack_team_id + "#" + self.slack_user_id


class Dao(object):
  def __init__(self, table_name):
    client = boto3.resource('dynamodb')
    self.table = client.Table(table_name)

  def get_spotify_track(self, spotify_track):
    """
    :param spotify_track: SpotifyTrack
    :return: SpotifyTrack
    """
    self.table.get_item(
      Key={
        'PK': spotify_track.PK,
        'SK': spotify_track.SK
      }
    )

  def insert_spotify_tracks(self, track_ids):
    for track_id in track_ids:
      if self.get_spotify_track(track_id) is None:
        self.insert_spotify_track(track_id)

  def insert_spotify_track(self, spotify_track):
    """
    :param spotify_track: SpotifyTrack
    :return:
    """
    self.table.put_item(Item={**spotify_track.__dict__})

  def blind_write(self, some_dict):
    self.table.put_item(Item={**some_dict})
