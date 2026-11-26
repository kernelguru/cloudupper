"""Dünner async-Wrapper um die rclone-CLI."""
from __future__ import annotations

import asyncio
import configparser
import json
import re
import threading
from pathlib import Path, PurePosixPath

from . import config

NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]{0,63}$")
_conf_lock = threading.Lock()


class RcloneError(RuntimeError):
    pass


def base_cmd() -> list[str]:
    return [config.RCLONE_BIN, "--config", str(config.RCLONE_CONFIG)]


async def run(args: list[str], timeout: float = 120) -> str:
    proc = await asyncio.create_subprocess_exec(
        *base_cmd(), *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RcloneError("rclone hat nicht rechtzeitig geantwortet")
    if proc.returncode != 0:
        msg = err.decode(errors="replace").strip().splitlines()
        raise RcloneError(msg[-1] if msg else f"rclone Exit-Code {proc.returncode}")
    return out.decode(errors="replace")


async def version() -> str:
    try:
        out = await run(["version"], timeout=10)
        return out.splitlines()[0].replace("rclone ", "")
    except Exception:  # noqa: BLE001
        return "nicht gefunden"


# ------------------------------------------------------------------ Pfade
def clean_rel(path: str | None) -> str:
    """Normalisiert einen relativen Pfad und verbietet '..'."""
    parts = []
    for part in PurePosixPath("/" + (path or "")).parts[1:]:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("Ungültiger Pfad")
        parts.append(part)
    return "/".join(parts)


def local_path(rel: str | None) -> Path:
    root = config.DATA_DIR.resolve()
    p = (root / clean_rel(rel)).resolve()
    if p != root and root not in p.parents:
        raise ValueError("Pfad liegt außerhalb des Datenverzeichnisses")
    return p


def target(remote: str, rel: str | None) -> str:
    """Erzeugt ein rclone-Ziel. Leerer remote = lokales Datenverzeichnis."""
    if not remote:
        return str(local_path(rel))
    if not NAME_RE.match(remote):
        raise ValueError("Ungültiger Cloud-Name")
    if remote not in remote_names():
        raise ValueError(f"Cloud '{remote}' ist nicht konfiguriert")
    return f"{remote}:{clean_rel(rel)}"


def label(remote: str, rel: str | None) -> str:
    return f"{remote or 'Server'}:/{clean_rel(rel)}"


BWLIMIT_RE = re.compile(r"^\d+(\.\d+)?[KMGkmg]?$")


# ------------------------------------------------------------------ Config
def _read_conf() -> configparser.RawConfigParser:
    cp = configparser.RawConfigParser(interpolation=None)
    cp.optionxform = str  # Groß-/Kleinschreibung erhalten
    cp.read(config.RCLONE_CONFIG)
    return cp


def remote_names() -> list[str]:
    with _conf_lock:
        return _read_conf().sections()


def list_remotes() -> list[dict]:
    with _conf_lock:
        cp = _read_conf()
        return [{"name": s, "type": cp.get(s, "type", fallback="?")} for s in cp.sections()]


def write_remote(name: str, fields: dict[str, str]) -> None:
    if not NAME_RE.match(name):
        raise ValueError("Name darf nur Buchstaben, Ziffern, '_', '-' und '.' enthalten")
    with _conf_lock:
        cp = _read_conf()
        if cp.has_section(name):
            cp.remove_section(name)
        cp.add_section(name)
        for k, v in fields.items():
            cp.set(name, k, str(v))
        tmp = config.RCLONE_CONFIG.with_suffix(".tmp")
        with tmp.open("w") as f:
            cp.write(f)
        tmp.chmod(0o600)
        tmp.replace(config.RCLONE_CONFIG)


def delete_remote(name: str) -> None:
    with _conf_lock:
        cp = _read_conf()
        if not cp.remove_section(name):
            raise ValueError("Unbekannte Cloud")
        tmp = config.RCLONE_CONFIG.with_suffix(".tmp")
        with tmp.open("w") as f:
            cp.write(f)
        tmp.replace(config.RCLONE_CONFIG)


async def config_create(name: str, rtype: str, params: dict[str, str]) -> None:
    if not NAME_RE.match(name):
        raise ValueError("Ungültiger Name")
    if not re.match(r"^[a-z0-9]+$", rtype):
        raise ValueError("Ungültiger Typ")
    args = ["config", "create", name, rtype]
    for k, v in params.items():
        if not re.match(r"^[a-z0-9_]+$", k):
            raise ValueError(f"Ungültiger Parameter: {k}")
        args.append(f"{k}={v}")
    args += ["--non-interactive", "--obscure"]
    out = await run(args, timeout=60)
    # Bei fehlenden Angaben liefert rclone eine Rückfrage als JSON
    try:
        q = json.loads(out)
        if isinstance(q, dict) and q.get("State"):
            opt = q.get("Option") or {}
            raise RcloneError(f"rclone benötigt weitere Angabe: {opt.get('Name')} – {opt.get('Help', '')[:200]}")
    except json.JSONDecodeError:
        pass


# ------------------------------------------------------------------ Remote-Operationen
async def lsjson(remote: str, rel: str, dirs_only: bool = True, modtime: bool = False) -> list[dict]:
    args = ["lsjson", target(remote, rel), "--no-mimetype"]
    if not modtime:
        args.append("--no-modtime")
    if dirs_only:
        args.append("--dirs-only")
    out = await run(args, timeout=120)
    items = json.loads(out or "[]")
    return [{"name": i["Name"], "dir": i["IsDir"], "size": i.get("Size", -1),
             "mtime": i.get("ModTime")} for i in items]


async def stat(remote: str, rel: str) -> dict:
    out = await run(["lsjson", "--stat", "--no-mimetype", target(remote, rel)], timeout=60)
    i = json.loads(out)
    return {"name": i["Name"], "dir": i["IsDir"], "size": i.get("Size", -1)}


async def delete(remote: str, rel: str, is_dir: bool) -> None:
    if not clean_rel(rel):
        raise ValueError("Das Wurzelverzeichnis kann nicht gelöscht werden")
    await run(["purge" if is_dir else "deletefile", target(remote, rel)], timeout=600)


async def rename(remote: str, rel: str, new_name: str) -> str:
    rel = clean_rel(rel)
    if not rel or not new_name or "/" in new_name or new_name in (".", ".."):
        raise ValueError("Ungültiger Name")
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    new_rel = f"{parent}/{new_name}" if parent else new_name
    await run(["moveto", target(remote, rel), target(remote, new_rel)], timeout=600)
    return new_rel


async def link(remote: str, rel: str) -> str:
    out = await run(["link", target(remote, rel)], timeout=60)
    return out.strip()


async def mkdir(remote: str, rel: str) -> None:
    await run(["mkdir", target(remote, rel)], timeout=60)


async def about(remote: str) -> dict:
    out = await run(["about", f"{remote}:", "--json"], timeout=60)
    return json.loads(out)
