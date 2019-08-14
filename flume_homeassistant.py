from datetime import datetime, timedelta
import json

import jwt
from ratelimit import limits
import requests


def format_datetime(time):
    return time.isoformat(' ', 'seconds')


class FlumeClient(object):
    API_BASE = "https://api.flumetech.com/"
    TOKEN_PATH = "oauth/token"
    DEVICES_PATH = 'users/{}/devices'
    NOTIFICATIONS_PATH = 'users/{}/notifications'
    QUERY_PATH = 'users/{}/devices/{}/query'
    TOKENS_FILE = 'flume_tokens'

    queries = [
        {
            "request_id": "today",
            "bucket": "DAY",
            "since_datetime": format_datetime(datetime.today()),
        },
        {
            "request_id": "this_month",
            "bucket": "MON",
            "since_datetime": format_datetime(datetime.today()),
        },
        {
            "request_id": "last_60_min",
            "operation": "SUM",
            "bucket": "MIN",
            "since_datetime": format_datetime(datetime.now() - timedelta(minutes=60)),
        },
        {
            "request_id": "last_24_hrs",
            "operation": "SUM",
            "bucket": "HR",
            "since_datetime": format_datetime(datetime.now() - timedelta(hours=23)),
        },
        {
            "request_id": "current_min",
            "bucket": "MIN",
            "since_datetime": format_datetime(datetime.now()),
        },
    ]

    def __init__(self, creds=None):
        self.creds = creds
        self.tokens = {}
        self.access_dict = {}
        self.device_id = ''
        self.user_id = ''
        self.headers = {'content-type': 'application/json'}

        try:
            with open(self.TOKENS_FILE) as tokens_file:
                self.tokens = json.load(tokens_file)
        except FileNotFoundError:
            print('Tokens file not found')
        except json.decoder.JSONDecodeError:
            print('Invalid JSON in tokens file')

        if self.tokens.get('access_token'):
            self.load_tokens(self.tokens)
            self.verify_token()
        else:
            self.fetch_tokens()

        self.user_id = self.access_dict['user_id']

        # Get device ID

        response = requests.get(url=self.API_BASE + self.DEVICES_PATH.format(self.user_id),
                                headers=self.headers).json()
        self.device_id = [d['id'] for d in response['data'] if d['type'] == 2][0]

    # Authorization token handling

    def token_request(self, payload):
        response = requests.post(url=self.API_BASE + self.TOKEN_PATH,
                                 json=payload,
                                 headers=self.headers).json()
        return response['data'][0]

    def verify_token(self):
        if 'exp' not in self.access_dict:
            self.access_dict = jwt.decode(self.tokens['access_token'], verify=False)

        expiry = datetime.fromtimestamp(self.access_dict['exp'])
        if expiry <= datetime.now() + timedelta(hours=1):
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': self.tokens['refresh_token'],
                'client_id': self.creds['client_id'],
                'client_secret': self.creds['client_secret']
            }
            self.load_tokens(self.token_request(payload))
            self.write_token_file()

    def fetch_tokens(self):
        payload = dict(self.creds, **{"grant_type": "password"})
        self.load_tokens(self.token_request(payload))
        self.write_token_file()

    def load_tokens(self, tokens):
        self.tokens = tokens
        self.access_dict = jwt.decode(self.tokens['access_token'], verify=False)
        self.headers.update({"Authorization": "Bearer " + self.tokens['access_token']})

    def write_token_file(self):
        with open(self.TOKENS_FILE, 'w') as tokens_file:
            tokens_file.write(json.dumps(self.tokens))

    # Flume API interaction

    @limits(calls=120, period=3600)
    def get_usage(self):
        self.verify_token()

        query_path = self.QUERY_PATH.format(self.user_id, self.device_id)
        response = requests.post(url=self.API_BASE + query_path,
                                 headers=self.headers,
                                 json={'queries': self.queries})
        values = response.json()['data'][0]
        return {k: v[0]['value'] for k, v in values.items()}
