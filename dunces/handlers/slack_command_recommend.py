# Escaped: <@U1234|user> <#C1234|general>
from dataclasses import asdict
from dunces.common import CIPHER_SUITE, DAO, RECOMMENDATION_SERVICE, get_single_match
from urllib.parse import parse_qs
import json
import re

from dunces.models import SlackRequest, UserRecommendation


def return_message(text):
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
            "text": f"{text}"
          }
        }
      ]
    })
  }


def handler(event, context):
  DAO.put_dictionary("audit", "recommend_event", event)
  params = dict(parse_qs(event['body']))
  DAO.put_dictionary("audit", "recommend_event_params", params)
  req = SlackRequest.from_command_request(params)
  DAO.put_dictionary("audit", "recommend_request", asdict(req))

  if req.text == "help":
    return return_message(f'/recommend view "Some Movie"\n'
                          f'/recommend view recent\n'
                          f'/recommend "Some Movie"')

  rec_search = get_single_match("view \"(.*)\"", req.text)

  if rec_search:
    rec = RECOMMENDATION_SERVICE.get_recommendation(req.team_id, rec_search)
    return return_message(f'searched {rec_search}:\n {str(rec)}')

  if req.text.startswith("view recent") or req.text.startswith("view popular"):
    recs = RECOMMENDATION_SERVICE.get_recommendations(req.team_id)
    return return_message(f'view recent:\n{str(recs)}')

  new_rec = get_single_match("\"(.*)\"", req.text)

  if new_rec:
    user_rec = UserRecommendation(req.team_id, req.user_id, new_rec)
    rec = RECOMMENDATION_SERVICE.insert_user_recommendation(user_rec)
    return return_message(f'inserted:\n {str(rec)}')

  return return_message(f'Sorry, I did not understand that. /recommend help')



