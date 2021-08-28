from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import pytz


@dataclass
class DynamoClass:
  PK: str = field(init=False)
  SK: str = field(init=False)
  data_type: str = field(init=False)


@dataclass
class Recommendation(DynamoClass):
  slack_team_id: str
  slack_user_id: [str]
  title: str
  count_recommends: int
  create_time: str = datetime.now(timezone.utc).isoformat()

  def __post_init__(self):
    self.PK = f'TEAM#{self.slack_team_id}'
    self.SK = f'RECOMMENDATION#{self.title.upper()}'
    self.data_type = 'Recommendation'


@dataclass
class SpotifyTrack(DynamoClass):
  spotify_track_id: str
  spotify_playlist_id: str
  slack_team_id: str
  slack_user_id: str = None  # Some old playlist items were added before auditing occurred
  create_time: str = datetime.now(timezone.utc).isoformat()
  slack_team_user_id: str = field(init=False)

  def __post_init__(self):
    self.PK = f'PLAYLIST#{self.slack_team_id}#{self.spotify_playlist_id}'
    self.SK = f'TRACK#{self.spotify_track_id}'
    self.data_type = 'SpotifyTrack'
    self.slack_team_user_id = f'USER#{self.slack_team_id}#{self.slack_user_id}'

  def get_date(self):
    return datetime.fromisoformat(self.create_time)\
      .replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Central'))\
      .strftime('%B %-d, %Y')


@dataclass
class SlackUser(DynamoClass):
  slack_team_id: str
  slack_user_id: str
  spotify_user_name_encrypt: str = None
  spotify_refresh_token_encrypt: str = None
  create_time: str = datetime.now(timezone.utc).isoformat()

  def __post_init__(self):
    self.PK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.SK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.data_type = 'SlackUser'


@dataclass
class SlackChannel(DynamoClass):
  slack_team_id: str
  slack_channel_id: str
  spotify_playlist_id: str = None
  create_time: str = datetime.now(timezone.utc).isoformat()

  def __post_init__(self):
    self.PK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
    self.SK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
    self.data_type = 'SlackChannel'


@dataclass
class SlackTeam(DynamoClass):
  slack_team_id: str
  slack_oauth_token_encrypt: str = None

  def __post_init__(self):
    self.PK = f'TEAM#{self.slack_team_id}'
    self.SK = f'TEAM#{self.slack_team_id}'
    self.data_type = 'SlackTeam'


class SlackEventType(Enum):
  MESSAGE = 'message'
  APP_MENTION = 'app_mention'


class SlackRequest:
  def __init__(self, request):
    event = request.get('event', {})
    self.team_id: str = request.get('team_id', event.get('team'))
    self.channel_id: str = event.get('channel')
    self.user_id: str = event.get('user')
    self.type: SlackEventType = SlackEventType[event.get('type', '').upper()]
    self.is_bot_message: bool = event.get('bot_id', None) is not None
    self.text = event.get('text')
