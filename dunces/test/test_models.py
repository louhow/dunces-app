from unittest import TestCase

from dunces.models import Recommendation, UserRecommendation
from time import sleep


class TestModels(TestCase):
  def test_recommendations(self):
    rec1 = Recommendation("team", "rec1", [UserRecommendation("team", "user1", "rec1"), UserRecommendation("team", "user2", "rec1")])
    sleep(1)
    rec2 = Recommendation("team", "rec2", [UserRecommendation("team", "user1", "rec2")])
    recs = [
      rec1,
      rec2
    ]

    print()

    print(rec1.create_time)
    print(rec2.create_time)

    print()
    recs.sort(key=lambda x: x.count_recommendations, reverse=True)
    for rec in recs:
      print(f'-{str(rec)}')
