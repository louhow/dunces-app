from dunces.helpers.dao import Dao
from dunces.helpers.recommendation_service import RecommendationService
from dunces.helpers.secure import CipherSuite

import os
import re

SUCCESS = {
  "statusCode": 200,
  "headers": {
    'Content-Type': 'text/html',
  }
}

DAO = Dao(os.environ['DYNAMODB_TABLE'])
CIPHER_SUITE = CipherSuite(os.environ['APP_KEY'])
RECOMMENDATION_SERVICE = RecommendationService(DAO)


def get_single_match(some_pattern, some_str):
  z = re.match(some_pattern, some_str)
  return z.group(1) if z and len(z.groups()) >= 1 else None
