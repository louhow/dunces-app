from dataclasses import dataclass, field
from datetime import datetime, timezone
import os


@dataclass
class SpotifyTrack:
  spotify_track_id: str
  slack_team_id: str
  slack_user_id: str
  slack_team_user_id: str = field(init=False)
  create_time: str = datetime.now(timezone.utc).isoformat()
  spotify_playlist_id: str = os.environ['SPOTIFY_THREAD_PLAYLIST_ID']
  PK: str = field(init=False)
  SK: str = field(init=False)

  def __post_init__(self):
    self.PK = f'PLAYLIST#{self.slack_team_id}#{self.spotify_playlist_id}'
    self.SK = f'TRACK#{self.spotify_track_id}'
    self.slack_team_user_id = f'USER#{self.slack_team_id}#{self.slack_user_id}'


@dataclass
class SlackUser:
  slack_team_id: str
  slack_user_id: str
  spotify_user_name_encrypt: str
  spotify_refresh_token_encrypt: str
  PK: str = field(init=False)
  SK: str = field(init=False)

  def __post_init__(self):
    self.PK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.SK = f'USER#{self.slack_team_id}#{self.slack_user_id}'


@dataclass
class SlackChannel:
  slack_team_id: str
  slack_channel_id: str
  spotify_playlist_id: str = None
  PK: str = field(init=False)
  SK: str = field(init=False)

  def __post_init__(self):
    self.PK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
    self.SK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
