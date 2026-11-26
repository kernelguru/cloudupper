"""Zeitgesteuerte Uploads: einmalig, an Wochentagen oder im Intervall."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta

from . import config, rclone
from .jobs import ACTIVE, make_copy_jobs, manager

log = logging.getLogger("cloudupper.schedules")
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


@dataclass
class Schedule:
    name: str
    items: list[str]           # relative Pfade unter /data
    remote: str                # Ziel-Cloud ("" = Server)
    path: str                  # Zielordner
    timing: dict               # siehe validate_timing()
    move: bool = False         # nach Upload auf dem Server löschen
    bwlimit: str = ""          # z.B. "10M"
    enabled: bool = True
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    created: float = field(default_factory=time.time)
    next_run: float | None = None
    last_run: float | None = None
    last_status: str = ""
    last_jobs: list[str] = field(default_factory=list)

    def public(self) -> dict:
        d = asdict(self)
        states = [manager.jobs[j].status for j in self.last_jobs if j in manager.jobs]
        d["last_result"] = {s: states.count(s) for s in set(states)}
        d["description"] = describe(self.timing)
        d["dest_label"] = rclone.label(self.remote, self.path)
        return d


# ---------------------------------------------------------------- Zeitberechnung
def _tz(t: dict):
    """Zeitzone des Browsers, in der der Termin eingegeben wurde (Fallback: TZ des Servers)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(t["tz"]) if t.get("tz") else config.TZINFO
    except Exception:  # noqa: BLE001
        return config.TZINFO


def _parse_local(s: str, tz=None) -> datetime:
    """'2026-11-27T02:00' in der Zeitzone des Zeitplans interpretieren."""
    dt = datetime.fromisoformat(s)
    return dt.replace(tzinfo=tz or config.TZINFO) if dt.tzinfo is None else dt


def _hm(s: str) -> tuple[int, int]:
    h, m = s.split(":")[:2]
    h, m = int(h), int(m)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError("Ungültige Uhrzeit")
    return h, m


def validate_timing(t: dict) -> dict:
    kind = t.get("type")
    tzname = str(t.get("tz") or "")[:64]
    if tzname:
        from zoneinfo import ZoneInfo
        try:
            ZoneInfo(tzname)
        except Exception:  # noqa: BLE001
            tzname = ""
    extra = {"tz": tzname} if tzname else {}
    if kind == "once":
        _parse_local(t["at"])
        return {"type": "once", "at": t["at"], **extra}
    if kind == "weekly":
        _hm(t["time"])
        days = sorted({int(d) for d in t.get("days", []) if 0 <= int(d) <= 6})
        if not days:
            raise ValueError("Mindestens einen Wochentag wählen")
        return {"type": "weekly", "time": t["time"], "days": days, **extra}
    if kind == "interval":
        hours = float(t.get("hours", 0))
        if not 0.25 <= hours <= 24 * 30:
            raise ValueError("Intervall zwischen 15 Minuten und 30 Tagen")
        out = {"type": "interval", "hours": hours, **extra}
        if t.get("start"):
            _parse_local(t["start"])
            out["start"] = t["start"]
        return out
    raise ValueError("Unbekannte Zeitplan-Art")


def next_after(s: Schedule, after: float) -> float | None:
    t = s.timing
    if t["type"] == "once":
        return None if s.last_run else _parse_local(t["at"], _tz(t)).timestamp()
    if t["type"] == "weekly":
        h, m = _hm(t["time"])
        base = datetime.fromtimestamp(after, _tz(t))
        for add in range(0, 8):
            day = base + timedelta(days=add)
            cand = day.replace(hour=h, minute=m, second=0, microsecond=0)
            if cand.weekday() in t["days"] and cand.timestamp() > after:
                return cand.timestamp()
        return None
    if t["type"] == "interval":
        step = t["hours"] * 3600
        start = _parse_local(t["start"], _tz(t)).timestamp() if t.get("start") else s.created + step
        if start > after:
            return start
        n = int((after - start) // step) + 1
        return start + n * step
    return None


def describe(t: dict) -> str:
    try:
        if t["type"] == "once":
            return "Einmalig am " + _parse_local(t["at"], _tz(t)).strftime("%d.%m.%Y um %H:%M")
        if t["type"] == "weekly":
            days = t["days"]
            if days == list(range(7)):
                d = "Täglich"
            elif days == [0, 1, 2, 3, 4]:
                d = "Werktags"
            elif days == [5, 6]:
                d = "Am Wochenende"
            else:
                d = ", ".join(WEEKDAYS[i] for i in days)
            return f"{d} um {t['time']} Uhr"
        h = t["hours"]
        return f"Alle {int(h * 60)} Minuten" if h < 1 else f"Alle {h:g} Stunden"
    except Exception:  # noqa: BLE001
        return "?"


# ---------------------------------------------------------------- Verwaltung
class Scheduler:
    def __init__(self) -> None:
        self.items: dict[str, Schedule] = {}
        self._task: asyncio.Task | None = None

    def load(self) -> None:
        try:
            raw = json.loads(config.SCHEDULES_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            raw = []
        now = time.time()
        for d in raw:
            s = Schedule(**d)
            if s.enabled:
                # Verpasste Einmal-Termine liefern einen Zeitpunkt in der Vergangenheit
                # und laufen daher direkt nach dem Start nach.
                s.next_run = next_after(s, now)
            self.items[s.id] = s
        self._task = asyncio.get_event_loop().create_task(self._loop())

    def save(self) -> None:
        tmp = config.SCHEDULES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps([asdict(s) for s in self.items.values()], indent=1))
        tmp.replace(config.SCHEDULES_FILE)

    def list(self) -> list[dict]:
        return [s.public() for s in sorted(self.items.values(), key=lambda s: (s.next_run or 9e18, s.name))]

    def upsert(self, data: dict, sid: str | None = None) -> Schedule:
        items = [rclone.clean_rel(i) for i in data.get("items", []) if rclone.clean_rel(i)]
        if not items:
            raise ValueError("Keine Dateien oder Ordner ausgewählt")
        for i in items:
            rclone.local_path(i)
        rclone.target(data.get("remote", ""), data.get("path", ""))  # Ziel prüfen
        bw = (data.get("bwlimit") or "").strip()
        if bw and not rclone.BWLIMIT_RE.match(bw):
            raise ValueError("Bandbreite z.B. als 10M oder 500K angeben")
        fields = dict(
            name=(data.get("name") or "").strip()[:80] or items[0].rsplit("/", 1)[-1],
            items=items, remote=data.get("remote", ""), path=rclone.clean_rel(data.get("path", "")),
            timing=validate_timing(data.get("timing") or {}), move=bool(data.get("move")),
            bwlimit=bw, enabled=bool(data.get("enabled", True)),
        )
        if sid:
            s = self.items[sid]
            for k, v in fields.items():
                setattr(s, k, v)
            if fields["timing"]["type"] == "once":
                s.last_run = None  # neuer Termin → wieder ausführbar
        else:
            s = Schedule(**fields)
            self.items[s.id] = s
        now = time.time()
        nxt = next_after(s, now) if s.enabled else None
        if s.enabled and (nxt is None or nxt < now - 60):
            if not sid:
                self.items.pop(s.id, None)
            raise ValueError("Der Termin liegt in der Vergangenheit")
        s.next_run = nxt
        self.save()
        return s

    def set_enabled(self, sid: str, enabled: bool) -> Schedule:
        s = self.items[sid]
        s.enabled = enabled
        if enabled and s.timing["type"] == "once" and s.last_run:
            s.last_run = None
        s.next_run = next_after(s, time.time()) if enabled else None
        if enabled and (s.next_run is None or s.next_run < time.time() - 60):
            s.next_run = None
            s.enabled = False
            raise ValueError("Der Termin liegt in der Vergangenheit – bitte neuen Zeitpunkt wählen")
        self.save()
        return s

    def delete(self, sid: str) -> None:
        self.items.pop(sid, None)
        self.save()

    def run_now(self, sid: str) -> Schedule:
        s = self.items[sid]
        self._execute(s, manual=True)
        self.save()
        return s

    # ------------------------------------------------------------ Ausführung
    def _execute(self, s: Schedule, manual: bool = False) -> None:
        now = time.time()
        running = [j for j in s.last_jobs if j in manager.jobs and manager.jobs[j].status in ACTIVE]
        if running:
            s.last_status = f"Übersprungen – {len(running)} Auftrag/Aufträge laufen noch"
        else:
            existing = [i for i in s.items if rclone.local_path(i).exists()]
            missing = len(s.items) - len(existing)
            flags = ["--bwlimit", s.bwlimit] if s.bwlimit else []
            try:
                jobs = make_copy_jobs("", [(i, None) for i in existing], s.remote, s.path,
                                      move=s.move, origin=f"schedule:{s.id}", flags=flags) if existing else []
                s.last_jobs = [j.id for j in jobs]
                s.last_status = f"{len(jobs)} Auftrag/Aufträge gestartet"
                if missing:
                    s.last_status += f", {missing} Quelle(n) nicht gefunden"
            except Exception as e:  # noqa: BLE001
                s.last_status = f"Fehler: {e}"
        s.last_run = now
        if not manual:
            if s.timing["type"] == "once":
                s.enabled = False
            s.next_run = next_after(s, now) if s.enabled else None
        log.info("Zeitplan %s (%s): %s", s.name, s.id, s.last_status)

    async def _loop(self) -> None:
        while True:
            try:
                now = time.time()
                due = [s for s in self.items.values() if s.enabled and s.next_run and s.next_run <= now]
                for s in due:
                    self._execute(s)
                if due:
                    self.save()
            except Exception:  # noqa: BLE001
                log.exception("Fehler im Zeitplaner")
            await asyncio.sleep(20)


scheduler = Scheduler()
