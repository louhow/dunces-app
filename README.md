# Dunces App

## Setup

```bash
mkvirtualenv --python `which python3` dunces-app
pip install -r requirements.txt
npm install -g serverless
npm install --save serverless-python-requirements
```

## Deploy

In order to deploy the endpoint simply run

```bash
serverless deploy
```
