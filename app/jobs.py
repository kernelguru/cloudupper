"""Auftragswarteschlange mit Fortschritt, Abbruch, Wiederholung und Persistenz."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field

import httpx

from . import config, rclone, torbox

log = logging.getLogger("cloudupper.jobs")

ACTIVE = ("queued", "running")


@dataclass
class Job:
    title: str
    spec: dict
    source_label: str = ""
    dest_label: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = "queued"  # queued | running | done | failed | canceled
    bytes: int = 0
    total: int = 0
    speed: float = 0.0
    eta: float | None = None
    current: str = ""
    error: str = ""
    origin: str = ""  # z.B. "schedule:<id>"
    created: float = field(default_factory=time.time)
    started: float | None = None
    finished: float | None = None

    def public(self) -> dict:
        d = asdict(self)
        d.pop("spec")
        d["kind"] = self.spec.get("op")
        d["progress"] = (self.bytes / self.total) if self.total else (1.0 if self.status == "done" else 0.0)
        return d


class JobManager:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._procs: dict[str, asyncio.subprocess.Process] = {}
        self._sem: asyncio.Semaphore | None = None

    # -------------------------------------------------------------- Persistenz
    def load(self) -> None:
        try:
            raw = json.loads(config.JOBS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            raw = []
        for d in raw:
            d.pop("progress", None)
            d.pop("kind", None)
            job = Job(**d)
            self.jobs[job.id] = job
        # Unterbrochene Aufträge nach Neustart fortsetzen
        for job in self.jobs.values():
            if job.status in ACTIVE:
                job.status = "queued"
                self._start(job)

    def save(self) -> None:
        data = [asdict(j) for j in list(self.jobs.values())[-300:]]
        tmp = config.JOBS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(config.JOBS_FILE)

    # -------------------------------------------------------------- API
    def submit(self, job: Job) -> Job:
        self.jobs[job.id] = job
        self._start(job)
        self.save()
        return job

    def list(self) -> list[dict]:
        return [j.public() for j in sorted(self.jobs.values(), key=lambda j: j.created, reverse=True)]

    def cancel(self, job_id: str) -> None:
        job = self.jobs[job_id]
        if job.status not in ACTIVE:
            return
        proc = self._procs.get(job_id)
        if proc and proc.returncode is None:
            proc.terminate()
        task = self._tasks.get(job_id)
        if task:
            task.cancel()
        job.status = "canceled"
        job.finished = time.time()
        self.save()

    def retry(self, job_id: str) -> Job:
        old = self.jobs[job_id]
        if old.status in ACTIVE:
            return old
        old.status, old.error, old.bytes, old.total = "queued", "", 0, 0
        old.speed, old.eta, old.started, old.finished, old.current = 0, None, None, None, ""
        self._start(old)
        self.save()
        return old

    def remove(self, job_id: str) -> None:
        self.cancel(job_id)
        job = self.jobs.pop(job_id, None)
        if job:
            _cleanup(job)
        self.save()

    def clear_finished(self) -> None:
        for jid in [j.id for j in self.jobs.values() if j.status not in ACTIVE]:
            _cleanup(self.jobs.pop(jid))
        self.save()

    # -------------------------------------------------------------- Ausführung
    def _start(self, job: Job) -> None:
        self._tasks[job.id] = asyncio.get_event_loop().create_task(self._run(job))

    async def _run(self, job: Job) -> None:
        if self._sem is None:
            self._sem = asyncio.Semaphore(config.MAX_PARALLEL)
        try:
            async with self._sem:
                if job.status != "queued":
                    return
                job.status, job.started = "running", time.time()
                self.save()
                await self._execute(job)
                job.status = "done"
                job.bytes = max(job.bytes, job.total)
        except asyncio.CancelledError:
            job.status = "canceled"
        except Exception as e:  # noqa: BLE001
            log.exception("Auftrag %s fehlgeschlagen", job.id)
            job.status, job.error = "failed", str(e) or e.__class__.__name__
        finally:
            job.finished = time.time()
            job.speed, job.eta = 0, None
            self._tasks.pop(job.id, None)
            self._procs.pop(job.id, None)
            self.save()
            if job.status in ("done", "failed"):
                asyncio.get_event_loop().create_task(notify(job))

    async def _execute(self, job: Job) -> None:
        spec = job.spec
        if spec["op"] == "copy":
            if spec.get("is_dir"):
                verb = "move" if spec.get("move") else "copy"
                extra = ["--delete-empty-src-dirs"] if spec.get("move") else []
            else:
                verb = "moveto" if spec.get("move") else "copyto"
                extra = []
            await self._rclone(job, [verb, spec["src"], spec["dst"], *extra, *spec.get("flags", [])])
            _cleanup(job)
        elif spec["op"] == "torbox":
            job.current = "Link wird bei TorBox angefordert…"
            url = await torbox.request_link(spec["kind"], spec["item_id"], spec.get("file_id"))
            job.current = ""
            await self._rclone(job, ["copyurl", url, spec["dst"], *spec.get("flags", [])])
        else:
            raise RuntimeError(f"Unbekannte Operation {spec['op']}")

    async def _rclone(self, job: Job, args: list[str]) -> None:
        cmd = [*rclone.base_cmd(), *args, "--use-json-log", "--stats", "1s",
               "--stats-log-level", "NOTICE", *config.RCLONE_FLAGS]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
            limit=4 * 1024 * 1024,
        )
        self._procs[job.id] = proc
        last_error = ""
        assert proc.stderr
        async for raw in proc.stderr:
            line = raw.decode(errors="replace").strip()
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                if line:
                    last_error = line
                continue
            stats = entry.get("stats")
            if stats:
                job.bytes = int(stats.get("bytes") or 0)
                job.total = int(stats.get("totalBytes") or job.total or 0)
                job.speed = float(stats.get("speed") or 0)
                job.eta = stats.get("eta")
                transferring = stats.get("transferring") or []
                if transferring:
                    job.current = transferring[0].get("name", "")
            elif entry.get("level") in ("error", "critical"):
                last_error = entry.get("msg", "")
        rc = await proc.wait()
        if job.status == "canceled":
            raise asyncio.CancelledError
        if rc != 0:
            raise RuntimeError(last_error or f"rclone beendet mit Code {rc}")


def make_copy_jobs(src_remote: str, items: list[tuple[str, bool | None]], dest_remote: str,
                   dest_path: str, move: bool = False, origin: str = "",
                   flags: list[str] | None = None) -> list[Job]:
    """Erzeugt (und startet) Kopier-/Verschiebe-Aufträge für Dateien und Ordner.

    items: (relativer Pfad in src_remote, ist_ordner) – bei lokaler Quelle wird is_dir ermittelt.
    """
    dest_dir = rclone.clean_rel(dest_path)
    jobs = []
    for rel, is_dir in items:
        rel = rclone.clean_rel(rel)
        if not rel:
            raise ValueError("Das Wurzelverzeichnis kann nicht direkt übertragen werden")
        if not src_remote:
            p = rclone.local_path(rel)
            if not p.exists():
                raise ValueError(f"Nicht gefunden: {rel}")
            is_dir = p.is_dir()
        name = rel.rsplit("/", 1)[-1]
        dst_rel = f"{dest_dir}/{name}" if dest_dir else name
        if src_remote == dest_remote and rclone.clean_rel(dst_rel) == rel:
            raise ValueError(f"Quelle und Ziel sind identisch: {rel}")
        job = Job(
            title=name,
            source_label=rclone.label(src_remote, rel),
            dest_label=rclone.label(dest_remote, dst_rel),
            origin=origin,
            spec={"op": "copy", "src": rclone.target(src_remote, rel),
                  "dst": rclone.target(dest_remote, dst_rel), "is_dir": bool(is_dir),
                  "move": move, "flags": flags or []},
        )
        jobs.append(manager.submit(job))
    return jobs


def _cleanup(job: Job) -> None:
    """Entfernt Zwischenspeicher von Geräte-Uploads."""
    d = job.spec.get("cleanup_dir")
    if d and str(d).startswith(str(config.STAGING_DIR)):
        shutil.rmtree(d, ignore_errors=True)


async def notify(job: Job) -> None:
    if not config.NOTIFY_URL:
        return
    ok = job.status == "done"
    text = f"{'✅' if ok else '❌'} {job.title}"
    if not ok:
        text += f"\n{job.error}"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(config.NOTIFY_URL, content=text.encode(),
                         headers={"Title": "CloudUpper", "Tags": "cloud"})
    except Exception:  # noqa: BLE001
        log.warning("Benachrichtigung fehlgeschlagen")


manager = JobManager()
