# Dunces App

A slack app that allows you to automatically add shared spotify songs to a channel's playlist.

## Setup

```bash
pyenv virtualenv 3.11 dunces-app-3.11
source activate dunces-app-3.11 
pip install -r requirements.txt
npm install -g serverless
npm install --save serverless-python-requirements
```
## Test

```bash
docker-compose up -d
pip install -e . # I think this is run once (from pytest best practices doc - https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html)
pytest --pyargs dunces 

# at one point I used  this flag - but it was broken and current tests do not require env vars
# pytest -c tests/config_test.ini
```


## Deploy

In order to deploy the endpoint simply run

```bash
serverless deploy # this may take 15-20 minutes the first time it's run - https://github.com/serverless/serverless-python-requirements/issues/561
```

```
App URL: https://api.slack.com/apps/A01KVM95JH2

Required Scopes - https://api.slack.com/apps/A4W5DQL7M/update-to-granular-scopes?

app_mentions:read
View messages that directly mention @sandboxbot in conversations that the app is in

channels:history
View messages and other content in public channels that sandbox-bot has been added to

chat:write
Send messages as @some-bot

groups:history
View messages and other content in private channels that sandbox-bot has been added to

links:read
View spotify.com and youtube.com URLs in messages

im:history
View messages and other content in direct messages that sandbox-bot has been added to

mpim:history
```
