# Escaped: <@U1234|user> <#C1234|general>
from dataclasses import asdict
from dunces.common import CIPHER_SUITE, DAO, SUCCESS
from urllib.parse import parse_qs
import json

from dunces.models import SlackRequest


def handler(event, context):
  DAO.put_dictionary("audit", "recommend_event", event)
  params = dict(parse_qs(event['body']))
  request = SlackRequest.from_command_request(params)
  DAO.put_dictionary("audit", "recommend_event_params", params)
  DAO.put_dictionary("audit", "recommend_request", asdict(request))

  return {
    "statusCode": 200,
    "headers": {
      'Content-Type': 'application/json',
    },
    "body": json.dumps({
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• {request.text}"
          }
        }
      ]
    })
  }

