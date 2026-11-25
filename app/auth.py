"""Signierte Tokens für Session-Cookie und OAuth-State."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from . import config

COOKIE = "cu_session"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign(payload: dict) -> str:
    body = _b64(json.dumps({**payload, "iat": int(time.time())}).encode())
    mac = hmac.new(config.secret_key(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"


def verify(token: str | None, max_age: int) -> dict | None:
    if not token or "." not in token:
        return None
    body, mac = token.rsplit(".", 1)
    expected = hmac.new(config.secret_key(), body.encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(expected, _unb64(mac)):
            return None
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if time.time() - payload.get("iat", 0) > max_age:
        return None
    return payload


def auth_required() -> bool:
    return bool(config.APP_PASSWORD)


def check_password(password: str) -> bool:
    return hmac.compare_digest(password.encode(), config.APP_PASSWORD.encode())


def is_authenticated(cookie: str | None) -> bool:
    if not auth_required():
        return True
    return verify(cookie, config.SESSION_DAYS * 86400) is not None
