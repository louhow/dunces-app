from dataclasses import asdict
from typing import List, Type, TypeVar

from dacite import from_dict, Config as DaciteConfig
from boto3.dynamodb.conditions import Key
import boto3

from dunces.models import DynamoClass

T = TypeVar('T', bound=DynamoClass)
DACITE_CONFIG = DaciteConfig(check_types=False, type_hooks={List: List})


class DuplicateItemException(Exception):
  def __init__(self, existing_item: T):
    self.existing_item = existing_item

  def get_existing_item(self) -> T:
    return self.existing_item


class Dao(object):
  def __init__(self, table_name, public_key=None, private_key=None, endpoint_url=None):
    print('hi')
    print(table_name)
    if endpoint_url is not None:
      self.resource = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    elif public_key is not None and private_key is not None:
      session = boto3.Session(aws_access_key_id=public_key, aws_secret_access_key=private_key)
      self.resource = session.resource('dynamodb')
    else:
      self.resource = boto3.resource('dynamodb')

    self.table = self.resource.Table(table_name)

  def put_item(self, item: T) -> T:
    self.put_dictionary(item.PK, item.SK, asdict(item))
    return item

  def insert_item(self, item: T) -> T:
    r"""
    :param item: item to insert
    :return: item that was inserted
    :raises DuplicateItemException: when item partition/sort key combo already exist
    """
    try:
      self.table.put_item(
        Item={**{"PK": item.PK, "SK": item.SK}, **asdict(item)},
        ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
      )
      return item
    except self.resource.meta.client.exceptions.ConditionalCheckFailedException as ex:
      raise DuplicateItemException(self.get_item(item))

  def get_item(self, item: T) -> T:
    some_dict = self.table.get_item(
      Key={
        'PK': item.PK,
        'SK': item.SK
      }
    )

    returned_item = some_dict.get('Item', None)

    return from_dict(item.__class__, returned_item, DACITE_CONFIG) if returned_item else None

  def get_items(self, pk, sk_starts_with, some_class: Type[T]) -> [T]:
    condition = Key('PK').eq(pk) & Key('SK').begins_with(sk_starts_with)
    response = self.table.query(KeyConditionExpression=condition)
    items = response.get('Items', None)
    return list(map(lambda item: from_dict(some_class, item, DACITE_CONFIG), items)) if items else []

  def put_dictionary(self, pk, sk, some_dict):
    return self.table.put_item(Item={**{"PK": pk, "SK": sk}, **some_dict})
