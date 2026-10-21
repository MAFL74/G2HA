import hashlib
import hmac
import secrets
import sqlite3
import time
from pathlib import Path


class OAuthStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS oauth_codes (code TEXT PRIMARY KEY, instance_id TEXT NOT NULL, client_id TEXT NOT NULL, redirect_uri TEXT NOT NULL, expires_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS oauth_tokens (token_hash TEXT PRIMARY KEY, instance_id TEXT NOT NULL, client_id TEXT NOT NULL, expires_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS oauth_refresh (token_hash TEXT PRIMARY KEY, instance_id TEXT NOT NULL, client_id TEXT NOT NULL)")

    def create_code(self, instance_id: str, client_id: str, redirect_uri: str) -> str:
        code = secrets.token_urlsafe(48)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO oauth_codes VALUES (?, ?, ?, ?, ?)", (code, instance_id, client_id, redirect_uri, time.time() + 300))
        return code

    def exchange_code(self, code: str, client_id: str, redirect_uri: str) -> tuple[str, str] | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT instance_id FROM oauth_codes WHERE code=? AND client_id=? AND redirect_uri=? AND expires_at>?", (code, client_id, redirect_uri, time.time())).fetchone()
            if not row:
                return None
            db.execute("DELETE FROM oauth_codes WHERE code=?", (code,))
            access = secrets.token_urlsafe(48)
            refresh = secrets.token_urlsafe(64)
            db.execute("INSERT INTO oauth_tokens VALUES (?, ?, ?, ?)", (hashlib.sha256(access.encode()).hexdigest(), row[0], client_id, time.time() + 3600))
            db.execute("INSERT INTO oauth_refresh VALUES (?, ?, ?)", (hashlib.sha256(refresh.encode()).hexdigest(), row[0], client_id))
            db.commit()
            return access, refresh

    def refresh_access(self, refresh: str, client_id: str) -> str | None:
        digest = hashlib.sha256(refresh.encode()).hexdigest()
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT instance_id FROM oauth_refresh WHERE token_hash=? AND client_id=?", (digest, client_id)).fetchone()
            if not row:
                return None
            access = secrets.token_urlsafe(48)
            db.execute("INSERT INTO oauth_tokens VALUES (?, ?, ?, ?)", (hashlib.sha256(access.encode()).hexdigest(), row[0], client_id, time.time() + 3600))
            db.commit()
            return access

    def validate_access(self, token: str) -> str | None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT instance_id FROM oauth_tokens WHERE token_hash=? AND expires_at>?", (digest, time.time())).fetchone()
        return row[0] if row else None


def valid_login(username: str, password: str) -> bool:
    expected_user = __import__("os").getenv("G2HA_OAUTH_USERNAME", "")
    expected_password = __import__("os").getenv("G2HA_OAUTH_PASSWORD", "")
    return bool(expected_user and expected_password and hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password))

