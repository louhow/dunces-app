from dataclasses import dataclass, field
from typing import List

from dunces.time import get_datetime, DateFormatter
from dunces.models.dynamo import DynamoClass


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
    return DateFormatter.to_date(self.create_time)


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
    return DateFormatter.to_date(self.create_time)
