import json

from flume_homeassistant import FlumeClient

CREDS_FILE = 'flume_creds.json'
TOKENS_FILE = 'flume_tokens'

if __name__ == '__main__':
    tokens = {}

    with open(TOKENS_FILE) as tokens_file:
        try:
            tokens = json.load(tokens_file)
        except json.decoder.JSONDecodeError as e:
            print('Invalid JSON file')

    access = tokens.get('access_token')

    if access:
        flume = FlumeClient(access_token=access)
    else:
        with open(CREDS_FILE) as creds_file:
            try:
                creds = json.load(creds_file)
            except json.decoder.JSONDecodeError as e:
                print('Invalid JSON file')
        if creds:
            flume = FlumeClient(creds=creds)
            with open(TOKENS_FILE, 'w') as tokens_file:
                tokens_file.write(json.dumps(flume.tokens))

    usage = flume.get_usage()

    pass