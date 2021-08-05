from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import os
import pytz


@dataclass
class SpotifyTrack:
  spotify_track_id: str
  slack_team_id: str
  slack_user_id: str = None  # Some old playlist items were added before auditing occurred
  slack_team_user_id: str = field(init=False)
  create_time: str = datetime.now(timezone.utc).isoformat()
  spotify_playlist_id: str = os.environ['SPOTIFY_THREAD_PLAYLIST_ID']
  PK: str = field(init=False)
  SK: str = field(init=False)

  def __post_init__(self):
    self.PK = f'PLAYLIST#{self.slack_team_id}#{self.spotify_playlist_id}'
    self.SK = f'TRACK#{self.spotify_track_id}'
    self.slack_team_user_id = f'USER#{self.slack_team_id}#{self.slack_user_id}'

  def get_date(self):
    return datetime.fromisoformat(self.create_time)\
      .replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Central'))\
      .strftime('%B %-d, %Y')


@dataclass
class SlackUser:
  slack_team_id: str
  slack_user_id: str
  spotify_user_name_encrypt: str = None
  spotify_refresh_token_encrypt: str = None
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


class SlackEventType(Enum):
  MESSAGE = 'message'
  APP_MENTION = 'app_mention'


class SlackRequest:
  def __init__(self, request):
    event = request.get('event', {})
    self.team_id: str = event.get('team')
    self.channel_id: str = event.get('channel')
    self.user_id: str = event.get('user')
    self.type: SlackEventType = SlackEventType[event.get('type', '').upper()]
    self.is_bot_message: bool = event.get('bot_id', None) is not None
    self.text = event.get('text', None)  # TODO remove None after removing link_shared events
