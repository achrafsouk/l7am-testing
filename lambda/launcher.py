import boto3
import json
import logging
import math
import os
import random


FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION')
TABLE_NAME = os.getenv('TABLE_NAME')

# Configure logger
logger = logging.getLogger('launchrequests')
logger.setLevel(logging.INFO)

# Configure boto3 stuff
session = boto3.Session()
table = session.resource('dynamodb').Table(TABLE_NAME)
lmbda = session.client('lambda')


def lambda_handler(event, context):
    random.seed(a=context.aws_request_id)
    # Get all resources from table
    resp = table.scan()
    for item in resp['Items']:
        logger.info("working on %s", item['hostname'])
        event = {
            'hostname': item['hostname'],
            'prefix': item['prefix'] if 'prefix' in item else '/',
            'protocol': item['protocol'],
            'min_requests_per_min': int(item['min_requests_per_min']),
            'max_requests_per_min':
                int(item['max_requests_per_min'] / item['parallelism']),
        }
        # Minimum amount of requests to send (lambda functions to launch)
        min = math.floor(
            int(item['parallelism']) - int(item['parallelism']) * 0.15)
        logger.info(
            "picking random int between %d and %d",
            min,
            int(item['parallelism']))
        # Launch lambda functions
        for i in range(random.randint(min, int(item['parallelism']))):
            logger.info(
                "launching function %d with payload '%s'",
                i,
                json.dumps(event))
            lmbda.invoke(
                FunctionName=FUNCTION_NAME,
                InvocationType='Event',
                Payload=json.dumps(event))
