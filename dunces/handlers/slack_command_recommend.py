# Escaped: <@U1234|user> <#C1234|general>
from dataclasses import asdict
from dunces.common import DAO, RECOMMENDATION_SERVICE, get_single_match
from dunces.helpers.dao import DuplicateItemException
from urllib.parse import parse_qs
import json

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
                          f'/recommend "Some Movie"\n'
                          f'@couch-bot assemble "Some Movie"')

  rec_search = get_single_match('view ["|“|”](.*)["|“|”]', req.text)

  if rec_search:
    rec = RECOMMENDATION_SERVICE.get_recommendation(req.team_id, rec_search)
    return return_message(f'searched {rec_search}:\n {str(rec)}')

  if req.text.startswith("view recent") or req.text.startswith("view popular"):
    recs = RECOMMENDATION_SERVICE.get_recommendations(req.team_id)
    if "recent" in req.text:
      recs.sort(key=lambda x: x.last_recommended_time, reverse=True)
    else:
      recs.sort(key=lambda x: x.count_recommendations, reverse=True)
    msg = '\n'.join([str(x) for x in recs[:10]])
    return return_message(f'{msg}')

  new_rec = get_single_match('["|“|”](.*)["|“|”]', req.text)

  if new_rec:
    user_rec = UserRecommendation(req.team_id, req.user_id, new_rec)
    try:
      rec = RECOMMENDATION_SERVICE.insert_user_recommendation(user_rec)
      return return_message(f'inserted:\n {str(rec)}')
    except DuplicateItemException as e:
      return return_message(f'You already recommended this: {e.get_existing_item()}')

  return return_message(f'Sorry, I did not understand that. /recommend help')
