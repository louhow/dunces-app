from dunces.dao.dynamo_dao import DynamoDao
from dunces.models.recommendation import UserRecommendation, Recommendation


class RecommendationService:
  def __init__(self, dao: DynamoDao):
    self.dao = dao
    
  def is_recommendation(self, text):
    return True

  def insert_user_recommendation(self, user_recommendation: UserRecommendation) -> Recommendation:
    """
    :param user_recommendation: user recommendation
    :return: recommendation with newest user recommendations list
    :raises DuplicateItemException[UserRecommendation]:
    """
    self.dao.insert_item(user_recommendation)
    recommendation = self.get_recommendation(user_recommendation.slack_team_id, user_recommendation.recommendation)
    if recommendation is None:
      new_recommendation = Recommendation(
        user_recommendation.slack_team_id,
        user_recommendation.recommendation,
        [user_recommendation]
      )
      self.dao.insert_item(new_recommendation)
      return new_recommendation
    else:
      recommendation.user_recommendations.append(user_recommendation)
      recommendation.count_recommendations += 1
      recommendation.last_recommended_time = user_recommendation.create_time
      self.dao.put_item(recommendation)
      return recommendation

  def get_recommendation(self, team_id: str, recommendation_text: str) -> Recommendation:
    return self.dao.get_item(Recommendation(team_id, recommendation_text, []))

  def get_recommendations(self, team_id) -> [Recommendation]:
    return self.dao.get_items(f'TEAM#{team_id}', 'RECOMMENDATION#', Recommendation)

  def get_user_recommendations(self, team_id: str, user_id: str) -> [UserRecommendation]:
    return self.dao.get_items(f'USER#{team_id}#{user_id}', 'RECOMMENDATION#', UserRecommendation)
