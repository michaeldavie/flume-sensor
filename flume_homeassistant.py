from datetime import datetime

import jwt
from oauthlib.oauth2 import LegacyApplicationClient
import requests
from requests_oauthlib import OAuth2Session


class FlumeClient(object):
    API_BASE = "https://api.flumetech.com/"
    TOKEN_PATH = "oauth/token"
    DEVICES_PATH = 'users/{}/devices'
    QUERY_PATH = 'users/{}/devices/{}/query'

    def __init__(self, access_token=None, creds=None):
        self.tokens = {}
        self.access_dict = {}
        self.device_id = ''
        self.headers = {'content-type': 'application/json'}

        if access_token:
            self.update_access_token(access_token)
        elif creds:
            self.request_tokens(creds=creds)

        self.get_device_id()

    def request_tokens(self, creds=None):
        payload = dict(creds, **{"grant_type": "password"})
        response = requests.post(url=self.API_BASE + self.TOKEN_PATH,
                                 json=payload,
                                 headers=self.headers).json()
        access = response['data'][0]['access_token']
        refresh = response['data'][0]['refresh_token']
        self.update_access_token(access)
        self.tokens['refesh_token'] = refresh

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
