from dataclasses import dataclass, field

from dunces.time import get_datetime, DateFormatter
from dunces.models.dynamo import DynamoClass


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
    return DateFormatter.to_date(self.create_time)
