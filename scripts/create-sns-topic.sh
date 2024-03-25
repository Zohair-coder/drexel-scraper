#!/bin/bash
export AWS_DEFAULT_REGION=us-east-1
aws --endpoint-url=http://localhost:4566 sns create-topic --name DrexelScheduler