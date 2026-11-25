"""OAuth-Definitionen der unterstützten Cloud-Dienste (rclone-kompatibel)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

PROVIDERS: dict[str, dict] = {
    "drive": {
        "label": "Google Drive",
        "rclone_type": "drive",
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "https://www.googleapis.com/auth/drive",
        "extra_auth": {"access_type": "offline", "prompt": "consent"},
        "config": {"scope": "drive"},
        "console": "https://console.cloud.google.com/apis/credentials",
    },
    "onedrive": {
        "label": "Microsoft OneDrive",
        "rclone_type": "onedrive",
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scope": "Files.Read Files.ReadWrite Files.Read.All Files.ReadWrite.All "
        "Sites.Read.All offline_access",
        "extra_auth": {"prompt": "select_account"},
        "config": {},
        "console": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
    },
    "hidrive": {
        "label": "STRATO HiDrive",
        "rclone_type": "hidrive",
        "auth_url": "https://my.hidrive.com/client/authorize",
        "token_url": "https://my.hidrive.com/oauth2/token",
        "scope": "user,rw",
        "extra_auth": {},
        "config": {"scope_access": "rw", "scope_role": "user"},
        "console": "https://developer.hidrive.com/",
    },
    "dropbox": {
        "label": "Dropbox",
        "rclone_type": "dropbox",
        "auth_url": "https://www.dropbox.com/oauth2/authorize",
        "token_url": "https://api.dropboxapi.com/oauth2/token",
        "scope": None,
        "extra_auth": {"token_access_type": "offline"},
        "config": {},
        "console": "https://www.dropbox.com/developers/apps",
    },
}


def authorize_url(provider: str, client_id: str, redirect_uri: str, state: str) -> str:
    p = PROVIDERS[provider]
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        **p["extra_auth"],
    }
    if p["scope"]:
        params["scope"] = p["scope"]
    return f"{p['auth_url']}?{urlencode(params)}"


def to_rclone_token(tok: dict) -> dict:
    expires_in = int(tok.get("expires_in", 3600))
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return {
        "access_token": tok["access_token"],
        "token_type": tok.get("token_type", "Bearer"),
        "refresh_token": tok.get("refresh_token", ""),
        "expiry": expiry.isoformat(),
    }


async def exchange_code(provider: str, code: str, client_id: str, client_secret: str,
                        redirect_uri: str) -> dict:
    p = PROVIDERS[provider]
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(p["token_url"], data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        })
    if r.status_code >= 400:
        raise RuntimeError(f"Token-Austausch fehlgeschlagen ({r.status_code}): {r.text[:300]}")
    return r.json()


async def onedrive_drive_info(access_token: str) -> dict:
    """rclone benötigt drive_id + drive_type für OneDrive."""
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get("https://graph.microsoft.com/v1.0/me/drive",
                        headers={"Authorization": f"Bearer {access_token}"})
    if r.status_code >= 400:
        raise RuntimeError(f"OneDrive-Laufwerk konnte nicht ermittelt werden: {r.text[:300]}")
    d = r.json()
    return {"drive_id": d["id"], "drive_type": d.get("driveType", "personal")}


async def remote_config(provider: str, token: dict, client_id: str = "",
                        client_secret: str = "") -> dict:
    """Baut die rclone.conf-Sektion für einen OAuth-Dienst."""
    import json

    p = PROVIDERS[provider]
    cfg = {"type": p["rclone_type"], **p["config"], "token": json.dumps(token)}
    if client_id:
        cfg["client_id"] = client_id
        cfg["client_secret"] = client_secret
    if provider == "onedrive":
        cfg.update(await onedrive_drive_info(token["access_token"]))
    return cfg
