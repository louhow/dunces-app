from unittest import TestCase
from dataclasses import asdict
import pytest

from dunces.helpers.dao import Dao, DuplicateItemException
from dunces.models import SpotifyTrack, Recommendation, SlackUserRecommendation


class TestDao(TestCase):
  dao = Dao("dunces-app-local", endpoint_url="http://localhost:4566")

  @pytest.fixture(autouse=True)
  def run_around_tests(self):
    self._truncate_data()
    yield
    assert True

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

  def test_get_nested_dataclass_items(self):
    recommendation = Recommendation(
      "slack_team_id",
      "title",
      [SlackUserRecommendation("slack_user_id", "some note")]
    )
    self.dao.put_item(recommendation)
    actual = self.dao.get_items(recommendation.PK, Recommendation)
    assert len(actual) is 1
    TestCase().assertDictEqual(asdict(actual[0]), asdict(recommendation))

  def _truncate_data(self):
    scan = None
    with self.dao.table.batch_writer() as batch:
      count = 0
      while scan is None or 'LastEvaluatedKey' in scan:
        if scan is not None and 'LastEvaluatedKey' in scan:
          scan = self.dao.table.scan(
            ProjectionExpression='PK, SK',
            ExclusiveStartKey=scan['LastEvaluatedKey'],
          )
        else:
          scan = self.dao.table.scan(ProjectionExpression='PK, SK')

        for item in scan['Items']:
          if count % 5000 == 0:
            print(count)
          batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
          count = count + 1
