#!/bin/sh
set -eu

exec python - <<'PY'
import json
import os
import uvicorn

try:
    with open('/data/options.json', encoding='utf-8') as f:
        options = json.load(f)
except FileNotFoundError:
    options = {}

mapping = {
    'environment': 'G2HA_ENV',
    'oauth_username': 'G2HA_OAUTH_USERNAME',
    'oauth_password': 'G2HA_OAUTH_PASSWORD',
    'oauth_client_id': 'G2HA_OAUTH_CLIENT_ID',
}
for source, target in mapping.items():
    value = options.get(source)
    if value is not None and value != '':
        os.environ[target] = str(value)

os.environ.setdefault('G2HA_ENV', 'production')
os.environ.setdefault('G2HA_OAUTH_DB', '/data/oauth.sqlite3')
uvicorn.run('relay.g2ha.app:app', host='0.0.0.0', port=8000)
PY
