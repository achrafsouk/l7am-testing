import base64
import datetime
import json
import logging
import math
import random
import time
import urllib.parse
import urllib3
import uuid


MINS_IN_DAY = 24 * 60

# Setup logging
logger = logging.getLogger('requestsender')
logger.setLevel(logging.INFO)

# Header names
HEADER_NAMES = (
    'accept',
    'accept-encoding',
    'accept-language',
    'user-agent',
)
# Load headers
HEADERS = {}
for h in HEADER_NAMES:
    with open('headers-{}.txt'.format(h), 'r') as fp:
        HEADERS[h] = []
        for line in fp.read().splitlines():
            if len(line.strip()) > 0:
                HEADERS[h].append(line.strip())

# Load paths
with open('simulate_paths.json', 'r') as fp:
    paths = json.load(fp)


# Get a random header (1 prevalent header, others with less representation)
def get_rand_header(headers):
    pct = random.randrange(60, 80)
    r = random.randrange(0, 100)
    if (r <= pct):
        h = headers[0]
    else:
        h = random.choice(headers[1:])
    return h


# Get a random path
def get_rand_path():
    r = random.randrange(0, 100)
    if (r <= 70):
        p = paths[0]
    else:
        p = random.choice(paths[1:])

    return random.choice(p)


# Update url for request
def update_path(request: dict, prefix: str):
    url = urllib.parse.urlsplit(request['url'])
    request['headers']['referer'] = request['url']
    request['url'] = urllib.parse.urljoin(
        "{}://{}".format(url.scheme, url.netloc),
        "{}{}".format(prefix, get_rand_path()).replace('//', '/'))
    return request


# Prepare the first request
def prepare_first_request(protocol: str, hostname: str, prefix: str):
    urlbase = "{}://{}".format(protocol, hostname)
    params = {
        'method': 'GET',
        'headers': {},
        'url': urllib.parse.urljoin(
                urlbase,
                '{}{}'.format(prefix, '/').replace('//', '/')),
    }

    for h in HEADER_NAMES:
        params['headers'][h] = get_rand_header(HEADERS[h])
    params['headers']['Cookie'] = "sid={}; tracker={}; r={}".format(
        str(uuid.uuid4()),
        base64.b64encode(str(uuid.uuid4()).encode('ascii')),
        random.random())

    return params


# Calculate request count based on current minute
def calculate_request_count(min: int, max: int, minute: int):
    if not minute:
        now = datetime.datetime.utcnow()
        minute = now.hour * 60 + now.minute

    # Morning / Night bucket
    if minute <= MINS_IN_DAY * 0.33 or minute >= MINS_IN_DAY * 0.66:
        factor = random.randrange(35, 55) / 100 # 0.5
    # Lunch time bucket
    elif MINS_IN_DAY * 0.48 <= minute <= MINS_IN_DAY * 0.52:
        factor = random.randrange(70, 80) / 100 #0.75
    # Peak bucket
    else:
        factor = random.randrange(80, 100) / 100

    req_count = round(
                 min + factor * max * math.sin(minute / MINS_IN_DAY * math.pi))
             
    return req_count


"""
  lambda_handler(event, context)
  event:
   - min_requests_per_min
   - max_requests_per_min
   - protocol
   - hostname
"""
def lambda_handler(event, context):
    random.seed(context.aws_request_id)

    # Setup connection pool
    http = urllib3.PoolManager(retries=2, timeout=5)

    # Get how many requests we need to send in this 1-min execution
    request_count = calculate_request_count(
        int(event['min_requests_per_min']),
        int(event['max_requests_per_min']),
        None
    )

    requests_remaining = request_count
    req_avg_time_ms = 0
    for i in range(request_count):
        logger.info(
            "iteration %d of %d",
            i,
            request_count
        )
        # Calculate sleep time
        sleep_max_ms = int(
            context.get_remaining_time_in_millis() / 
            requests_remaining - req_avg_time_ms
        )
        logger.info(
            "maximum sleep time is %dms",
            sleep_max_ms
        )
        # Sleep if we are not in a rush
        if sleep_max_ms > 0:
            sleep_s = random.randrange(
                int(sleep_max_ms / 2),
                sleep_max_ms
            ) / 1000
            logger.info(
                "sleeping %fs before sending request",
                sleep_s
            )
            time.sleep(sleep_s)
        # Prepare request
        if i == 0:
            req = prepare_first_request(
                event['protocol'],
                event['hostname'],
                event['prefix']
            )
        else:
            req = update_path(req, event['prefix'])

        # Send request
        logger.info(
            "sending request to '%s' with ua '%s' and 'referer' %s",
            req['url'],
            req['headers']['user-agent'],
            req['headers']['referer'] if 'referer' in req['headers'] else ''
        )
        start = time.time()
        req['redirect'] = False
        try:
            resp = http.request(**req)
            status = resp.status
        except Exception as e:
            logger.info(
                "request failed with exeception %s",
                e
            )
            status = 999
            
        end = time.time()
        req_avg_time_ms = (req_avg_time_ms + (end-start) * 1000) / 2
        logger.info(
            "request finished in %ds with status code %d",
            (end - start),
            status
        )
        logger.info(
            "avg request time is at %dms",
            req_avg_time_ms
        )
        requests_remaining -= 1
    http.clear()    
    return
