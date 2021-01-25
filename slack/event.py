import json
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
import uuid

import boto3
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
  data = json.loads(event['body'])
  # TODO verify challenge
  if "challenge" in data:
    return {
      "statusCode": 200,
      "body": data["challenge"],
      "headers": {
        'Content-Type': 'text/html',
      }
    }

  try:
    client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
    client.chat_postMessage(channel='#testing', text=f"{data['event']['type']}")
    print(event)
  except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["ok"] is False
    assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
    print(f"Got an error: {e.response['error']}")
  finally:
    return {
      "statusCode": 200,
      "headers": {
        'Content-Type': 'text/html',
      }
    }
