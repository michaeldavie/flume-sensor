import json

from flume_homeassistant import FlumeClient

CREDS_FILE = 'flume_creds.json'

with open(CREDS_FILE) as creds_file:
    creds = json.load(creds_file)

if creds:
    flume = FlumeClient(creds=creds)
    print(json.dumps(flume.get_usage(), indent=4))
