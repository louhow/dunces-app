# Dunces App

## Setup

```bash
mkvirtualenv --python `which python3` dunces-app
pip install -r requirements.txt
npm install -g serverless
npm install --save serverless-python-requirements
```
## Test

```bash
docker-compose up -d
cd tests
python -m pytest -c config_test.ini
```


## Deploy

In order to deploy the endpoint simply run

```bash
serverless deploy
```

```
Required Scopes

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
