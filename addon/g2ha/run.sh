#!/bin/sh
set -eu

exec python - <<'PY'
import json
import logging
import os
import uvicorn


class G2HAAccessFormatter(logging.Formatter):
    """Timestamp access lines without copying OAuth query strings into logs."""

    def format(self, record):
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S%z")
        args = getattr(record, "args", ())
        if isinstance(args, tuple) and len(args) >= 5:
            client_addr, method, target, _, status_code = args[:5]
        else:
            client_addr = getattr(record, "client_addr", "-")
            request_line = getattr(record, "request_line", "")
            parts = request_line.split(" ", 2)
            method = parts[0] if parts else "-"
            target = parts[1] if len(parts) > 1 else "/"
            status_code = getattr(record, "status_code", "-")
        path = target.split("?", 1)[0]
        return f"{timestamp} INFO {client_addr} {method} {path} {status_code}"

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

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s %(levelprefix)s %(message)s",
            "use_colors": False,
        },
        "access": {"()": G2HAAccessFormatter},
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default", "stream": "ext://sys.stderr"},
        "access": {"class": "logging.StreamHandler", "formatter": "access", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "relay.g2ha": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["default"], "level": "INFO"},
}

uvicorn.run('relay.g2ha.app:app', host='0.0.0.0', port=8000, log_config=LOG_CONFIG)
PY

