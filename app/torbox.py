"""TorBox-API (https://api.torbox.app)."""
from __future__ import annotations

import httpx

from . import config

BASE = "https://api.torbox.app/v1/api"

# kind -> (Pfadsegment, ID-Parameter für requestdl)
KINDS = {
    "torrents": ("torrents", "torrent_id"),
    "webdl": ("webdl", "web_id"),
    "usenet": ("usenet", "usenet_id"),
}


class TorboxError(RuntimeError):
    pass


def _key() -> str:
    key = config.torbox_key()
    if not key:
        raise TorboxError("Kein TorBox-API-Key hinterlegt (Einstellungen)")
    return key


async def _request(method: str, path: str, **kw) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.request(method, f"{BASE}{path}",
                            headers={"Authorization": f"Bearer {_key()}"}, **kw)
    try:
        data = r.json()
    except ValueError:
        raise TorboxError(f"TorBox antwortet mit HTTP {r.status_code}")
    if r.status_code >= 400 or not data.get("success", False):
        raise TorboxError(data.get("detail") or data.get("error") or f"HTTP {r.status_code}")
    return data


def _normalize(item: dict) -> dict:
    files = item.get("files") or []
    progress = item.get("progress") or 0
    finished = bool(item.get("download_finished") or item.get("download_present"))
    return {
        "id": item.get("id"),
        "name": item.get("name") or "Unbenannt",
        "size": item.get("size") or sum(f.get("size", 0) for f in files),
        "progress": 1.0 if finished else float(progress),
        "state": item.get("download_state") or ("fertig" if finished else "unbekannt"),
        "ready": finished,
        "created": item.get("created_at"),
        "files": [
            {
                "id": f.get("id"),
                "name": f.get("name") or f.get("short_name"),
                "short_name": f.get("short_name") or (f.get("name") or "").rsplit("/", 1)[-1],
                "size": f.get("size", 0),
            }
            for f in files
        ],
    }


async def mylist(kind: str) -> list[dict]:
    seg, _ = KINDS[kind]
    data = await _request("GET", f"/{seg}/mylist", params={"bypass_cache": "true"})
    items = data.get("data") or []
    if isinstance(items, dict):
        items = [items]
    out = [_normalize(i) for i in items]
    out.sort(key=lambda i: i.get("created") or "", reverse=True)
    return out


async def request_link(kind: str, item_id: int, file_id: int | None) -> str:
    seg, id_param = KINDS[kind]
    params = {"token": _key(), id_param: item_id, "redirect": "false"}
    if file_id is None:
        params["zip_link"] = "true"
    else:
        params["file_id"] = file_id
    data = await _request("GET", f"/{seg}/requestdl", params=params)
    url = data.get("data")
    if not isinstance(url, str) or not url.startswith("http"):
        raise TorboxError("TorBox hat keinen Download-Link geliefert")
    return url


async def add(kind: str, value: str) -> dict:
    if kind == "magnet":
        return await _request("POST", "/torrents/createtorrent", data={"magnet": value})
    if kind == "link":
        return await _request("POST", "/webdl/createwebdownload", data={"link": value})
    raise TorboxError("Unbekannter Typ")


async def user() -> dict:
    data = await _request("GET", "/user/me")
    return data.get("data") or {}
