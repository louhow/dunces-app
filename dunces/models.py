from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List

import pytz


@dataclass
class DynamoClass:
  PK: str = field(init=False)
  SK: str = field(init=False)
  data_type: str = field(init=False)


@dataclass
class SlackUserRecommendation:
  slack_team_id: str
  slack_user_id: str
  recommendation: str
  recommendation_note: str = None
  create_time: str = datetime.now(timezone.utc).isoformat()


@dataclass
class Recommendation(DynamoClass):
  slack_team_id: str
  recommendation: str
  count_recommendations: int
  create_time: str = datetime.now(timezone.utc).isoformat()

  def __post_init__(self):
    self.PK = f'TEAM#{self.slack_team_id}'
    self.SK = f'RECOMMENDATION#{self.recommendation.upper()}'
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

  # TODO migrate PK/SK to TEAM#*/USER#*
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

  # TODO migrate PK/SK to TEAM#*/CHANNEL#*
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
  COMMAND = 'command'


@dataclass
class SlackRequest:
  team_id: str
  channel_id: str
  user_id: str
  type: str
  text: str
  is_bot_message: bool = False

  @classmethod
  def from_event_request(cls, event_request):
    event = event_request.get('event', {})
    return cls(
      event_request.get('team_id', event.get('team')),
      event.get('channel'),
      event.get('user'),
      event.get('type', '').upper(),
      event.get('text'),
      event.get('bot_id', None) is not None,
    )

  @classmethod
  def from_command_request(cls, params):
    return cls(
      params.get('team_id')[0],
      next(iter(params.get('channel_id', [])), None),
      params.get('user_id')[0],
      SlackEventType.COMMAND.value,
      params.get('text')[0]
    )

  def get_type(self) -> SlackEventType:
    return SlackEventType[self.type]
