import os

from slack_sdk import WebClient

from service.models import SlackTeam
from slack.event import DAO, CIPHER_SUITE

oauth_scope = ", ".join(["app_mentions:read", "channels:history", "chat:write", "groups:history", "links:read", "im:history", "mpim:history"])
client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
state = os.environ["APP_STATE"]


def html(content):
  return {
    "statusCode": 200,
    "body": content,
    "headers": {
      'Content-Type': 'text/html',
    }
  }


def pre_install(event, context):
  return html(f'<a href="https://slack.com/oauth/v2/authorize?scope={ oauth_scope }&client_id={ client_id }&state={ state }"><img alt=""Add to Slack"" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>')


def post_install(event, context):
  # Retrieve the auth code and state from the request params
  params = event['queryStringParameters']
  auth_code = params['code']
  received_state = params['state']

  # Exchange the authorization code for an access token with Slack
  response = WebClient().oauth_v2_access(
    client_id=client_id,
    client_secret=client_secret,
    code=auth_code
  )

  slack_team_id = response["team"]["id"]
  token = CIPHER_SUITE.encrypt(response["access_token"])

  DAO.insert_slack_team(SlackTeam(slack_team_id, token))

  # Don't forget to let the user know that auth has succeeded!
  return html("Auth complete!")
