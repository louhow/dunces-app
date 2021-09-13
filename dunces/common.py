from dunces.helpers.dao import Dao
from dunces.helpers.secure import CipherSuite

import os

SUCCESS = {
  "statusCode": 200,
  "headers": {
    'Content-Type': 'text/html',
  }
}

DAO = Dao(os.environ['DYNAMODB_TABLE'])
CIPHER_SUITE = CipherSuite(os.environ['APP_KEY'])