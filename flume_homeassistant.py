from datetime import datetime
import json

import jwt
import requests


class FlumeClient(object):
    API_BASE = "https://api.flumetech.com/"
    TOKEN_PATH = "oauth/token"
    DEVICES_PATH = 'users/{}/devices'
    QUERY_PATH = 'users/{}/devices/{}/query'
    TOKENS_FILE = 'flume_tokens'

    def __init__(self, creds=None):
        self.tokens = {}
        self.access_dict = {}
        self.device_id = ''
        self.headers = {'content-type': 'application/json'}

        try:
            with open(self.TOKENS_FILE) as tokens_file:
                self.tokens = json.load(tokens_file)
        except FileNotFoundError:
            print('Tokens file not found')
        except json.decoder.JSONDecodeError:
            print('Invalid JSON in tokens file')

        if self.tokens.get('access_token'):
            self.update_access_token(self.tokens.get('access_token'))
        elif creds:
            self.fetch_tokens(creds=creds)

        self.get_device_id()

    def fetch_tokens(self, creds=None):
        payload = dict(creds, **{"grant_type": "password"})
        response = requests.post(url=self.API_BASE + self.TOKEN_PATH,
                                 json=payload,
                                 headers=self.headers).json()
        access = response['data'][0]['access_token']
        refresh = response['data'][0]['refresh_token']
        self.update_access_token(access)
        self.tokens['refesh_token'] = refresh

        with open(self.TOKENS_FILE, 'w') as tokens_file:
            tokens_file.write(json.dumps(self.tokens))

    def update_access_token(self, access):
        self.tokens['access_token'] = access
        self.access_dict = jwt.decode(access, verify=False)
        self.headers.update({"Authorization": "Bearer " + access})

    def get_device_id(self):
        user_id = self.access_dict['user_id']
        response = requests.get(url=self.API_BASE + self.DEVICES_PATH.format(user_id),
                                headers=self.headers).json()
        self.device_id = [d['id'] for d in response['data'] if d['type'] == 2][0]

    def get_usage(self):
        queries = [
            {
                "bucket": "DAY",
                "since_datetime": datetime.today().replace(hour=0, minute=0, second=0).isoformat(' ', 'seconds'),
                "request_id": "today"
            },
            {
                "bucket": "MON",
                "since_datetime": datetime.today().replace(day=1, hour=0, minute=0, second=0).isoformat(' ', 'seconds'),
                "request_id": "this_month"
            }
        ]

        query_path = self.QUERY_PATH.format(self.access_dict['user_id'], self.device_id)
        response = requests.post(url=self.API_BASE + query_path,
                                 headers=self.headers,
                                 json={'queries': queries}).json()
        values = response['data'][0]
        return {k: v[0]['value'] for k, v in values.items()}
