from dataclasses import asdict
from typing import List, Type, TypeVar

from dacite import from_dict, Config as DaciteConfig
from boto3.dynamodb.conditions import Key
import boto3

from dunces.models import DynamoClass

T = TypeVar('T', bound=DynamoClass)
DACITE_CONFIG = DaciteConfig(check_types=False, type_hooks={List: List})


class Dao(object):
  def __init__(self, table_name, public_key=None, private_key=None, endpoint_url=None):
    if endpoint_url is not None:
      client = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    elif public_key is not None and private_key is not None:
      session = boto3.Session(aws_access_key_id=public_key, aws_secret_access_key=private_key)
      client = session.resource('dynamodb')
    else:
      client = boto3.resource('dynamodb')

    self.table = client.Table(table_name)

  def put_item(self, item: T) -> T:
    self.put_dictionary(item.PK, item.SK, asdict(item))
    return item

  def get_item(self, item: T) -> T:
    some_dict = self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )

    returned_item = some_dict.get('Item', None)

    return from_dict(item.__class__, returned_item, DACITE_CONFIG) if returned_item else None

  def get_items(self, pk, some_class: Type[T]) -> [T]:
    response = self.table.query(KeyConditionExpression=Key('PK').eq(pk))
    items = response.get('Items', None)
    return list(map(lambda item: from_dict(some_class, item, DACITE_CONFIG), items)) if items else []

  def put_dictionary(self, pk, sk, some_dict):
    return self.table.put_item(Item={**{"PK": pk, "SK": sk}, **some_dict})
