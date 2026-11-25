"""CloudUpper – Web-App zum Hochladen in Cloud-Speicher und Laden von TorBox."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth, config, providers, rclone, torbox
from .jobs import Job, manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cloudupper")
STATIC = Path(__file__).parent / "static"
UPLOAD_ID_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")


@asynccontextmanager
async def lifespan(_: FastAPI):
    config.ensure_dirs()
    manager.load()
    if not config.APP_PASSWORD:
        log.warning("APP_PASSWORD ist nicht gesetzt – die Oberfläche ist ungeschützt!")
    yield


app = FastAPI(title="CloudUpper", version=config.VERSION, lifespan=lifespan,
              docs_url="/api/docs", openapi_url="/api/openapi.json")

PUBLIC_API = {"/api/session", "/api/login", "/api/logout", "/api/oauth/callback"}


@app.middleware("http")
async def guard(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC_API:
        if not auth.is_authenticated(request.cookies.get(auth.COOKIE)):
            return JSONResponse({"detail": "Nicht angemeldet"}, status_code=401)
    return await call_next(request)


@app.exception_handler(ValueError)
async def value_error(_: Request, exc: ValueError):
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(rclone.RcloneError)
async def rclone_error(_: Request, exc: rclone.RcloneError):
    return JSONResponse({"detail": f"rclone: {exc}"}, status_code=502)


@app.exception_handler(torbox.TorboxError)
async def torbox_error(_: Request, exc: torbox.TorboxError):
    return JSONResponse({"detail": f"TorBox: {exc}"}, status_code=502)


def fmt_dest(remote: str, path: str) -> str:
    return f"{remote or 'Server'}:/{rclone.clean_rel(path)}"


# ====================================================================== Session
class Login(BaseModel):
    password: str


_failed: dict[str, int] = {}


@app.get("/api/session")
async def session(request: Request):
    return {
        "auth_required": auth.auth_required(),
        "authenticated": auth.is_authenticated(request.cookies.get(auth.COOKIE)),
    }


@app.post("/api/login")
async def login(body: Login, request: Request, response: Response):
    ip = request.client.host if request.client else "?"
    if not auth.auth_required():
        return {"ok": True}
    if not auth.check_password(body.password):
        _failed[ip] = _failed.get(ip, 0) + 1
        await asyncio.sleep(min(10, _failed[ip]))  # einfache Bremse gegen Brute-Force
        raise HTTPException(401, "Falsches Passwort")
    _failed.pop(ip, None)
    response.set_cookie(auth.COOKIE, auth.sign({"u": "admin"}), max_age=config.SESSION_DAYS * 86400,
                        httponly=True, samesite="lax", secure=request.url.scheme == "https")
    return {"ok": True}


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(auth.COOKIE)
    return {"ok": True}


@app.get("/api/status")
async def status():
    return {
        "version": config.VERSION,
        "rclone": await rclone.version(),
        "torbox": bool(config.torbox_key()),
        "data_dir": str(config.DATA_DIR),
        "download_dir": config.DOWNLOAD_SUBDIR,
        "auth": auth.auth_required(),
        "notify": bool(config.NOTIFY_URL),
    }


# ====================================================================== Browsen
@app.get("/api/browse")
async def browse(remote: str = "", path: str = "", dirs_only: bool = False):
    path = rclone.clean_rel(path)
    if not remote:
        p = rclone.local_path(path)
        if not p.is_dir():
            raise HTTPException(404, "Ordner nicht gefunden")
        entries = []
        for e in os.scandir(p):
            if e.name.startswith("."):
                continue
            try:
                is_dir = e.is_dir()
                if dirs_only and not is_dir:
                    continue
                st = e.stat()
                entries.append({"name": e.name, "dir": is_dir,
                                "size": -1 if is_dir else st.st_size, "mtime": st.st_mtime})
            except OSError:
                continue
    else:
        rclone.target(remote, path)  # validiert
        entries = await rclone.lsjson(remote, path, dirs_only)
    entries.sort(key=lambda e: (not e["dir"], e["name"].lower()))
    return {"remote": remote, "path": path, "entries": entries}


class MkdirBody(BaseModel):
    remote: str = ""
    path: str


@app.post("/api/mkdir")
async def mkdir(body: MkdirBody):
    if not body.remote:
        rclone.local_path(body.path).mkdir(parents=True, exist_ok=True)
    else:
        rclone.target(body.remote, body.path)
        await rclone.mkdir(body.remote, body.path)
    return {"ok": True}


class DeleteBody(BaseModel):
    items: list[str]


@app.post("/api/local/delete")
async def local_delete(body: DeleteBody):
    """Löscht Dateien/Ordner auf dem Server – nur auf ausdrücklichen Wunsch aus der Oberfläche."""
    root = config.DATA_DIR.resolve()
    targets = []
    for item in body.items:
        p = rclone.local_path(item)
        if p == root or not p.exists():
            raise HTTPException(400, f"Kann nicht gelöscht werden: {item}")
        targets.append(p)
    for p in targets:
        if p.is_dir() and not p.is_symlink():
            await asyncio.to_thread(shutil.rmtree, p)
        else:
            p.unlink()
        log.info("Gelöscht auf Wunsch: %s", p)
    return {"deleted": len(targets)}


# ====================================================================== Clouds
@app.get("/api/remotes")
async def remotes():
    return rclone.list_remotes()


@app.get("/api/remotes/{name}/about")
async def remote_about(name: str):
    rclone.target(name, "")
    try:
        return await rclone.about(name)
    except rclone.RcloneError as e:
        return {"error": str(e)}


@app.delete("/api/remotes/{name}")
async def remote_delete(name: str):
    rclone.delete_remote(name)
    return {"ok": True}


def redirect_uri(request: Request) -> str:
    base = config.BASE_URL or str(request.base_url).rstrip("/")
    return f"{base}/api/oauth/callback"


@app.get("/api/providers")
async def provider_list(request: Request):
    out = []
    for key, p in providers.PROVIDERS.items():
        cid, _ = config.oauth_client(key)
        out.append({"id": key, "label": p["label"], "oauth_ready": bool(cid),
                    "console": p["console"], "authorize_cmd": f'rclone authorize "{p["rclone_type"]}"'})
    return {"providers": out, "redirect_uri": redirect_uri(request)}


@app.get("/api/oauth/{provider}/start")
async def oauth_start(provider: str, name: str, request: Request):
    if provider not in providers.PROVIDERS:
        raise HTTPException(404, "Unbekannter Anbieter")
    if not rclone.NAME_RE.match(name):
        raise HTTPException(400, "Ungültiger Name")
    cid, _ = config.oauth_client(provider)
    if not cid:
        raise HTTPException(400, "Für diesen Anbieter sind keine OAuth-Zugangsdaten hinterlegt")
    ru = redirect_uri(request)
    state = auth.sign({"p": provider, "n": name, "r": ru})
    return {"url": providers.authorize_url(provider, cid, ru, state)}


@app.get("/api/oauth/callback")
async def oauth_callback(state: str = "", code: str = "", error: str = "",
                         error_description: str = ""):
    def back(msg: str, ok: bool = False):
        from urllib.parse import quote
        return RedirectResponse(f"/#clouds?{'ok' if ok else 'error'}={quote(msg)}")

    if error:
        return back(error_description or error)
    payload = auth.verify(state, 900)
    if not payload:
        return back("Ungültige oder abgelaufene Anmeldung – bitte erneut versuchen")
    provider, name, ru = payload["p"], payload["n"], payload["r"]
    cid, secret = config.oauth_client(provider)
    try:
        tok = await providers.exchange_code(provider, code, cid, secret, ru)
        cfg = await providers.remote_config(provider, providers.to_rclone_token(tok), cid, secret)
        rclone.write_remote(name, cfg)
    except Exception as e:  # noqa: BLE001
        log.exception("OAuth fehlgeschlagen")
        return back(str(e))
    return back(f"{providers.PROVIDERS[provider]['label']} als „{name}“ verbunden", ok=True)


class TokenBody(BaseModel):
    name: str
    provider: str
    token: str


@app.post("/api/remotes/token")
async def remote_from_token(body: TokenBody):
    """Token aus `rclone authorize "drive"` (eigener Rechner mit Browser) übernehmen."""
    if body.provider not in providers.PROVIDERS:
        raise HTTPException(400, "Unbekannter Anbieter")
    raw = body.token.strip()
    m = re.search(r"\{.*\}", raw, re.S)  # erlaubt das Einfügen der kompletten rclone-Ausgabe
    try:
        tok = json.loads(m.group(0) if m else raw)
        assert "access_token" in tok
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "Token ist kein gültiges JSON mit access_token")
    cfg = await providers.remote_config(body.provider, tok)
    rclone.write_remote(body.name, cfg)
    return {"ok": True}


class GenericBody(BaseModel):
    name: str
    type: str
    params: dict[str, str] = Field(default_factory=dict)


@app.post("/api/remotes/generic")
async def remote_generic(body: GenericBody):
    await rclone.config_create(body.name, body.type, body.params)
    return {"ok": True}


# ====================================================================== Einstellungen
def _mask(v: str) -> str:
    return (v[:4] + "…" + v[-4:]) if len(v) > 10 else ("•••" if v else "")


@app.get("/api/settings")
async def get_settings():
    s = config.load_settings()
    oauth = {}
    for key in providers.PROVIDERS:
        cid, secret = config.oauth_client(key)
        oauth[key] = {"client_id": cid, "client_secret": _mask(secret),
                      "from_env": config.oauth_from_env(key)}
    return {"torbox_api_key": _mask(config.torbox_key()),
            "torbox_from_env": bool(os.getenv("TORBOX_API_KEY")),
            "oauth": oauth, "has_settings": bool(s)}


class SettingsBody(BaseModel):
    torbox_api_key: str | None = None
    oauth: dict[str, dict[str, str]] | None = None


@app.put("/api/settings")
async def put_settings(body: SettingsBody):
    s = config.load_settings()
    if body.torbox_api_key is not None and "…" not in body.torbox_api_key:
        s["torbox_api_key"] = body.torbox_api_key.strip()
    if body.oauth:
        cur = s.setdefault("oauth", {})
        for key, val in body.oauth.items():
            if key not in providers.PROVIDERS:
                continue
            entry = cur.setdefault(key, {})
            if "client_id" in val:
                entry["client_id"] = val["client_id"].strip()
            sec = val.get("client_secret")
            if sec is not None and "…" not in sec and sec != "•••":
                entry["client_secret"] = sec.strip()
    config.save_settings(s)
    return {"ok": True}


# ====================================================================== Uploads
class ServerUpload(BaseModel):
    items: list[str]
    remote: str
    path: str = ""
    move: bool = False


@app.post("/api/upload/server")
async def upload_server(body: ServerUpload):
    dest_dir = rclone.clean_rel(body.path)
    created = []
    for item in body.items:
        src = rclone.local_path(item)
        if not src.exists() or src == config.DATA_DIR.resolve():
            raise HTTPException(400, f"Nicht gefunden: {item}")
        dst = rclone.target(body.remote, f"{dest_dir}/{src.name}")
        job = Job(
            title=src.name,
            source_label=f"Server:/{rclone.clean_rel(item)}",
            dest_label=fmt_dest(body.remote, f"{dest_dir}/{src.name}"),
            spec={"op": "copy", "src": str(src), "dst": dst, "is_dir": src.is_dir(), "move": body.move},
        )
        created.append(manager.submit(job).public())
    return {"jobs": created}


@app.put("/api/upload/device/{upload_id}")
async def upload_chunk(upload_id: str, request: Request, offset: int = 0):
    """Nimmt einen Datei-Abschnitt entgegen (resumable, umgeht Proxy-Limits)."""
    if not UPLOAD_ID_RE.match(upload_id):
        raise HTTPException(400, "Ungültige Upload-ID")
    part = config.STAGING_DIR / f"{upload_id}.part"
    size = part.stat().st_size if part.exists() else 0
    if offset != size:
        return JSONResponse({"detail": "Offset passt nicht", "size": size}, status_code=409)
    with part.open("ab") as f:
        async for chunk in request.stream():
            await asyncio.to_thread(f.write, chunk)
    return {"size": part.stat().st_size}


@app.get("/api/upload/device/{upload_id}")
async def upload_chunk_status(upload_id: str):
    if not UPLOAD_ID_RE.match(upload_id):
        raise HTTPException(400, "Ungültige Upload-ID")
    part = config.STAGING_DIR / f"{upload_id}.part"
    return {"size": part.stat().st_size if part.exists() else 0}


class CompleteBody(BaseModel):
    name: str
    size: int
    remote: str
    path: str = ""


@app.post("/api/upload/device/{upload_id}/complete")
async def upload_complete(upload_id: str, body: CompleteBody):
    if not UPLOAD_ID_RE.match(upload_id):
        raise HTTPException(400, "Ungültige Upload-ID")
    part = config.STAGING_DIR / f"{upload_id}.part"
    if not part.exists() or part.stat().st_size != body.size:
        raise HTTPException(400, "Upload unvollständig")
    name = body.name.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if name in ("", ".", ".."):
        name = "datei"
    rel = f"{rclone.clean_rel(body.path)}/{name}"
    dst = rclone.target(body.remote, rel)
    folder = config.STAGING_DIR / upload_id
    folder.mkdir(exist_ok=True)
    final = folder / name
    shutil.move(str(part), final)
    job = Job(title=name, source_label="Gerät", dest_label=fmt_dest(body.remote, rel),
              spec={"op": "copy", "src": str(final), "dst": dst, "is_dir": False,
                    "move": True, "cleanup_dir": str(folder)})
    return manager.submit(job).public()


# ====================================================================== TorBox
@app.get("/api/torbox/user")
async def torbox_user():
    u = await torbox.user()
    return {k: u.get(k) for k in ("email", "plan", "premium_expires_at", "total_downloaded")}


@app.get("/api/torbox/{kind}")
async def torbox_list(kind: str):
    if kind not in torbox.KINDS:
        raise HTTPException(404, "Unbekannte Liste")
    return await torbox.mylist(kind)


class TorboxAdd(BaseModel):
    type: str  # magnet | link
    value: str


@app.post("/api/torbox/add")
async def torbox_add(body: TorboxAdd):
    res = await torbox.add(body.type, body.value.strip())
    return {"ok": True, "detail": res.get("detail")}


class TorboxFile(BaseModel):
    item_id: int
    file_id: int | None = None
    name: str


class TorboxDownload(BaseModel):
    kind: str
    files: list[TorboxFile]
    remote: str = ""  # leer = Server
    path: str = ""


@app.post("/api/torbox/download")
async def torbox_download(body: TorboxDownload):
    if body.kind not in torbox.KINDS:
        raise HTTPException(400, "Unbekannte Liste")
    base = rclone.clean_rel(body.path)
    if not body.remote and not base:
        base = config.DOWNLOAD_SUBDIR
    created = []
    for f in body.files:
        rel = rclone.clean_rel(f"{base}/{f.name}")
        if f.file_id is None and not rel.endswith(".zip"):
            rel += ".zip"
        job = Job(
            title=rel.rsplit("/", 1)[-1],
            source_label="TorBox",
            dest_label=fmt_dest(body.remote, rel),
            spec={"op": "torbox", "kind": body.kind, "item_id": f.item_id,
                  "file_id": f.file_id, "dst": rclone.target(body.remote, rel)},
        )
        created.append(manager.submit(job).public())
    return {"jobs": created}


# ====================================================================== Aufträge
@app.get("/api/jobs")
async def jobs_list():
    return manager.list()


def _job(job_id: str):
    if job_id not in manager.jobs:
        raise HTTPException(404, "Auftrag nicht gefunden")


@app.post("/api/jobs/{job_id}/cancel")
async def job_cancel(job_id: str):
    _job(job_id)
    manager.cancel(job_id)
    return {"ok": True}


@app.post("/api/jobs/{job_id}/retry")
async def job_retry(job_id: str):
    _job(job_id)
    return manager.retry(job_id).public()


@app.delete("/api/jobs/{job_id}")
async def job_delete(job_id: str):
    _job(job_id)
    manager.remove(job_id)
    return {"ok": True}


@app.post("/api/jobs/clear")
async def jobs_clear():
    manager.clear_finished()
    return {"ok": True}


# ====================================================================== Frontend
@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC / "sw.js", media_type="application/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=STATIC), name="static")
