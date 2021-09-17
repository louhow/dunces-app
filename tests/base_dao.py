from unittest import TestCase
import pytest

from dunces.helpers.dao import Dao
from dunces.helpers.recommendation_service import RecommendationService


class TestBaseDao(TestCase):
  dao = Dao("dunces-app-local", endpoint_url="http://localhost:4566")
  recommendation_service = RecommendationService(dao)

  @pytest.fixture(autouse=True)
  def run_around_tests(self):
    self._truncate_data()
    yield
    assert True

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
