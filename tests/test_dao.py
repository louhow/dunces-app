from unittest import TestCase
from dataclasses import asdict

from dunces.helpers.dao import DuplicateItemException
from dunces.models import SpotifyTrack, Recommendation, UserRecommendation
from base_dao import TestBaseDao


class TestDao(TestBaseDao):
  def test_insert_same_item_twice_fails(self):
    track_to_insert = SpotifyTrack("track_id", "playlist_id", "slack_team_id")
    self.dao.insert_item(track_to_insert)
    try:
      self.dao.insert_item(track_to_insert)
      assert True is False
    except DuplicateItemException as e:
      TestCase().assertDictEqual(asdict(e.get_existing_item()), asdict(track_to_insert))

  def test_put_item(self):
    track_to_insert = SpotifyTrack("track_id", "playlist_id", "slack_team_id")
    assert self.dao.get_item(track_to_insert) is None
    track = self.dao.put_item(SpotifyTrack("track_id", "playlist_id", "slack_team_id"))
    assert self.dao.get_item(track) is not None

  def test_get_dataclass_items(self):
    recommendation = Recommendation(
      "slack_team_id",
      "title",
      [UserRecommendation("team", "user", "mhm")],
    )
    self.dao.put_item(recommendation)
    actual = self.dao.get_items(recommendation.PK, 'RECOMMENDATION#', Recommendation)
    assert len(actual) is 1
    TestCase().assertDictEqual(asdict(actual[0]), asdict(recommendation))
