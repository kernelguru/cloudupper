"""Zentrale Konfiguration (Umgebungsvariablen + persistente Einstellungen)."""
from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path

CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/config"))
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DOWNLOAD_SUBDIR = os.getenv("DOWNLOAD_SUBDIR", "downloads")
STAGING_DIR = Path(os.getenv("STAGING_DIR", str(CONFIG_DIR / "staging")))
RCLONE_CONFIG = Path(os.getenv("RCLONE_CONFIG_PATH", str(CONFIG_DIR / "rclone.conf")))
RCLONE_BIN = os.getenv("RCLONE_BIN", "rclone")
RCLONE_FLAGS = os.getenv("RCLONE_FLAGS", "").split()

APP_PASSWORD = os.getenv("APP_PASSWORD", "")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
MAX_PARALLEL = max(1, int(os.getenv("MAX_PARALLEL", "2")))
NOTIFY_URL = os.getenv("NOTIFY_URL", "")  # z.B. https://ntfy.sh/mein-topic
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))

try:
    from zoneinfo import ZoneInfo
    TZINFO = ZoneInfo(os.getenv("TZ") or "Europe/Berlin")
except Exception:  # noqa: BLE001 – unbekannte Zeitzone
    from datetime import timezone as _tz
    TZINFO = _tz.utc

SETTINGS_FILE = CONFIG_DIR / "settings.json"
SCHEDULES_FILE = CONFIG_DIR / "schedules.json"
JOBS_FILE = CONFIG_DIR / "jobs.json"
SECRET_FILE = CONFIG_DIR / "secret.key"

VERSION = "1.1.0"

_lock = threading.Lock()


def ensure_dirs() -> None:
    for d in (CONFIG_DIR, STAGING_DIR, RCLONE_CONFIG.parent):
        d.mkdir(parents=True, exist_ok=True)
    try:
        (DATA_DIR / DOWNLOAD_SUBDIR).mkdir(parents=True, exist_ok=True)
    except OSError as e:  # z.B. /data schreibgeschützt eingebunden
        import logging
        logging.getLogger("cloudupper").warning("Download-Ordner nicht anlegbar: %s", e)
    if not RCLONE_CONFIG.exists():
        RCLONE_CONFIG.touch(mode=0o600)


def secret_key() -> bytes:
    env = os.getenv("SECRET_KEY")
    if env:
        return env.encode()
    with _lock:
        if not SECRET_FILE.exists():
            SECRET_FILE.write_text(secrets.token_hex(32))
            SECRET_FILE.chmod(0o600)
        return SECRET_FILE.read_text().strip().encode()


# ---------------------------------------------------------------- Einstellungen
_ENV_OAUTH = {
    "drive": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
    "onedrive": ("ONEDRIVE_CLIENT_ID", "ONEDRIVE_CLIENT_SECRET"),
    "hidrive": ("HIDRIVE_CLIENT_ID", "HIDRIVE_CLIENT_SECRET"),
    "dropbox": ("DROPBOX_CLIENT_ID", "DROPBOX_CLIENT_SECRET"),
}


def load_settings() -> dict:
    with _lock:
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


def save_settings(data: dict) -> None:
    with _lock:
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.chmod(0o600)
        tmp.replace(SETTINGS_FILE)


def torbox_key() -> str:
    return os.getenv("TORBOX_API_KEY") or load_settings().get("torbox_api_key", "")


def oauth_client(provider: str) -> tuple[str, str]:
    env_id, env_secret = _ENV_OAUTH.get(provider, ("", ""))
    if env_id and os.getenv(env_id):
        return os.getenv(env_id, ""), os.getenv(env_secret, "")
    creds = load_settings().get("oauth", {}).get(provider, {})
    return creds.get("client_id", ""), creds.get("client_secret", "")


def oauth_from_env(provider: str) -> bool:
    env_id, _ = _ENV_OAUTH.get(provider, ("", ""))
    return bool(env_id and os.getenv(env_id))
