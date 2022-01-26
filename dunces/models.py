from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List

import pytz


def get_datetime():
  return datetime.now(timezone.utc).isoformat()


class DateFormatter:
  @staticmethod
  def get_date(iso_time):
    return datetime.fromisoformat(iso_time) \
      .replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Central')) \
      .strftime('%b %-d, %Y')


@dataclass
class DynamoClass:
  PK: str = field(init=False)
  SK: str = field(init=False)
  GSIPK1: str = field(init=False)
  GSISK1: str = field(init=False)
  data_type: str = field(init=False)


@dataclass
class UserRecommendation(DynamoClass):
  slack_team_id: str
  slack_user_id: str
  recommendation: str
  create_time: str = field(default_factory=get_datetime)

  # TODO decide
  def __post_init__(self):
    self.PK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.SK = f'RECOMMENDATION#{self.recommendation.upper()}'
    self.data_type = 'UserRecommendation'
    self.GSIPK1 = self.PK
    self.GSISK1 = self.create_time

  def __repr__(self):
    return f'<@{self.slack_user_id}> ({self.get_create_date()})'

  def get_create_date(self):
    return DateFormatter.get_date(self.create_time)


@dataclass
class Recommendation(DynamoClass):
  slack_team_id: str
  recommendation: str
  user_recommendations: List[UserRecommendation]
  create_time: str = field(default_factory=get_datetime)
  count_recommendations: int = field(init=False)
  last_recommended_time: str = field(init=False)

  # TODO decide
  def __post_init__(self):
    self.count_recommendations = len(self.user_recommendations)
    if self.user_recommendations:
      self.last_recommended_time = self.user_recommendations[len(self.user_recommendations)-1].create_time
    self.PK = f'TEAM#{self.slack_team_id}'
    self.SK = f'RECOMMENDATION#{self.recommendation.upper()}'
    self.GSIPK1 = self.PK
    self.GSISK1 = f'{self.count_recommendations:10}'
    self.data_type = 'Recommendation'

  def __repr__(self):
    user_rec_str = ', '.join([str(x) for x in self.user_recommendations])
    return f'{self.recommendation} ({self.count_recommendations}): {user_rec_str}'

  def get_create_date(self):
    return DateFormatter.get_date(self.create_time)


@dataclass
class SpotifyTrack(DynamoClass):
  spotify_track_id: str
  spotify_playlist_id: str
  slack_team_id: str
  slack_user_id: str = None  # Some old playlist items were added before auditing occurred
  slack_timestamp: str = None  # Some old tracks were added before we added this timestamp
  create_time: str = field(default_factory=get_datetime)
  slack_team_user_id: str = field(init=False)

  def __post_init__(self):
    self.PK = f'PLAYLIST#{self.slack_team_id}#{self.spotify_playlist_id}'
    self.SK = f'TRACK#{self.spotify_track_id}'
    self.GSIPK1 = self.slack_team_id
    self.GSISK1 = f'{self.create_time}'
    self.data_type = 'SpotifyTrack'
    self.slack_team_user_id = f'USER#{self.slack_team_id}#{self.slack_user_id}'

  def get_date(self):
    return DateFormatter.get_date(self.create_time)


@dataclass
class SlackUser(DynamoClass):
  slack_team_id: str
  slack_user_id: str
  spotify_user_name_encrypt: str = None
  spotify_refresh_token_encrypt: str = None
  create_time: str = field(default_factory=get_datetime)

  # TODO migrate PK/SK to TEAM#*/USER#*
  def __post_init__(self):
    self.PK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.SK = f'USER#{self.slack_team_id}#{self.slack_user_id}'
    self.data_type = 'SlackUser'
    self.GSIPK1 = self.slack_team_id
    self.GSISK1 = self.create_time


@dataclass
class SlackChannel(DynamoClass):
  slack_team_id: str
  slack_channel_id: str
  spotify_playlist_id: str = None
  create_time: str = field(default_factory=get_datetime)

  # TODO migrate PK/SK to TEAM#*/CHANNEL#*
  def __post_init__(self):
    self.PK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
    self.SK = f'CHANNEL#{self.slack_team_id}#{self.slack_channel_id}'
    self.data_type = 'SlackChannel'
    self.GSIPK1 = self.PK
    self.GSISK1 = self.create_time


@dataclass
class SlackTeam(DynamoClass):
  slack_team_id: str
  slack_oauth_token_encrypt: str = None
  create_time: str = field(default_factory=get_datetime)

  def __post_init__(self):
    self.PK = f'TEAM#{self.slack_team_id}'
    self.SK = f'TEAM#{self.slack_team_id}'
    self.data_type = 'SlackTeam'
    self.GSIPK1 = self.PK
    self.GSISK1 = self.SK


class SlackEventType(Enum):
  MESSAGE = 'message'
  APP_MENTION = 'app_mention'
  COMMAND = 'command'


# TODO break out SlackRecommendRequest and SlackEventRequest
@dataclass
class SlackRequest:
  team_id: str
  channel_id: str
  user_id: str
  type: str
  text: str
  event_timestamp: str = None
  event_thread_timestamp: str = None
  event_is_bot_message: bool = False
  command_trigger_id: str = None

  @classmethod
  def from_event_request(cls, event_request):
    event = event_request.get('event', {})
    return cls(
      team_id=event_request.get('team_id', event.get('team')),
      channel_id=event.get('channel'),
      user_id=event.get('user'),
      type=event.get('type', '').upper(),
      text=event.get('text'),
      event_timestamp=event.get('ts'),
      event_thread_timestamp=event.get('thread_ts', None),
      event_is_bot_message=event.get('bot_id', None) is not None,
    )

  @classmethod
  def from_command_request(cls, params):
    return cls(
      team_id=params.get('team_id')[0],
      channel_id=next(iter(params.get('channel_id', [])), None),
      user_id=params.get('user_id')[0],
      type=SlackEventType.COMMAND.value,
      text=params.get('text')[0],
      command_trigger_id=params.get('trigger_id')[0]
    )

  def get_type(self) -> SlackEventType:
    return SlackEventType[self.type]
