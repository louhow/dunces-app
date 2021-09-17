from dataclasses import asdict
from unittest import TestCase

from base_dao import TestBaseDao
from dunces.helpers.dao import DuplicateItemException
from dunces.models import UserRecommendation


class TestRecommendationService(TestBaseDao):
  def test_insert_same_user_rec_twice_fails(self):
    user_rec = UserRecommendation("slack team", "slack user", "my rec")
    self.recommendation_service.insert_user_recommendation(user_rec)
    try:
      self.recommendation_service.insert_user_recommendation(user_rec)
      assert True is False  # Never hit here
    except DuplicateItemException as e:
      pass

  def test_insert_two_recommendations(self):
    user_rec_1 = UserRecommendation("slack team", "user 1", "my rec")
    user_rec_2 = UserRecommendation("slack team", "user 2", "my rec")
    self.recommendation_service.insert_user_recommendation(user_rec_1)
    actual = self.recommendation_service.insert_user_recommendation(user_rec_2)
    assert actual.user_recommendations[0].slack_user_id == user_rec_1.slack_user_id
    assert actual.user_recommendations[1].slack_user_id == user_rec_2.slack_user_id

  def test_get_user_recommendations(self):
    user_rec = UserRecommendation("slack team", "user 1", "first rec")
    user_different_rec = UserRecommendation("slack team", "user 1", "second rec")
    self.recommendation_service.insert_user_recommendation(user_rec)
    self.recommendation_service.insert_user_recommendation(user_different_rec)
    actual = self.recommendation_service.get_user_recommendations(user_rec.slack_team_id, user_rec.slack_user_id)
    TestCase().assertDictEqual(asdict(actual[0]), asdict(user_rec))
    TestCase().assertDictEqual(asdict(actual[1]), asdict(user_different_rec))

  def test_get_recommendations(self):
    user_rec_1 = UserRecommendation("slack team", "user 1", "my rec")
    expected = self.recommendation_service.insert_user_recommendation(user_rec_1)
    actual = self.recommendation_service.get_recommendation(user_rec_1.slack_team_id, user_rec_1.recommendation)
    TestCase().assertDictEqual(asdict(actual), asdict(expected))

  def test_get_recommendations_from_same_team(self):
    user_rec1 = UserRecommendation("slack team", "user 1", "first rec")
    user_rec2 = UserRecommendation("slack team", "user 2", "second rec")
    rec1 = self.recommendation_service.insert_user_recommendation(user_rec1)
    rec2 = self.recommendation_service.insert_user_recommendation(user_rec2)
    actual = self.recommendation_service.get_recommendations(user_rec1.slack_team_id)
    TestCase().assertDictEqual(asdict(actual[0]), asdict(rec1))
    TestCase().assertDictEqual(asdict(actual[1]), asdict(rec2))
