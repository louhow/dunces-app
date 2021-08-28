#!/bin/sh

DYNAMODB_ENDPOINT=http://localstack-dynamodb:4566

aws --region us-east-1 --endpoint-url ${DYNAMODB_ENDPOINT} dynamodb create-table \
  --table-name dunces-app-local                                             \
  --attribute-definitions '[
    {
      "AttributeName": "PK",
      "AttributeType": "S"
    },
    {
      "AttributeName": "SK",
      "AttributeType": "S"
    }]'                                                                             \
  --key-schema '[
    {
      "AttributeName": "PK",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "SK",
      "KeyType": "RANGE"
    }
  ]'                                                                             \
  --provisioned-throughput '{
    "ReadCapacityUnits": 1,
    "WriteCapacityUnits": 1
  }'
