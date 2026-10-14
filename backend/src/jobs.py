"""Background jobs for large inference files.

Single-replica demo: threads + JSON metadata files under <uploads>/jobs so
status survives a process restart. Concurrency is bounded by
MAX_CONCURRENT_JOBS (429 when full). For multi-worker production replace
with Redis/Celery or equivalent durable queue with retries and per-user
quotas. Jobs are NOT a privacy boundary — same retention and transport
rules as sync predict apply (see docs/DEPLOYMENT.md).
"""
import json
import os
import threading
import time
import uuid
from pathlib import Path

_LOCK = threading.Lock()
_MAX_CONCURRENT = int(os.environ.get("AIPFL_MAX_CONCURRENT_JOBS", "2"))


_UPLOAD_ROOT: str | None = None
_BOOT_TIME = time.time()
STALE_AFTER_SECONDS = float(os.environ.get("AIPFL_JOB_STALE_SECONDS", "3600"))


def jobs_dir(upload_dir=None):
    root = upload_dir or _UPLOAD_ROOT or os.environ.get("AIPFL_UPLOAD_DIR", "uploads")
    d = Path(root) / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def configure(upload_dir):
    global _UPLOAD_ROOT
    _UPLOAD_ROOT = str(upload_dir)


def _meta_path(job_id, upload_dir=None):
    return jobs_dir(upload_dir) / f"{job_id}.json"


def _read_meta(job_id, upload_dir=None):
    p = _meta_path(job_id, upload_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"job_id": job_id, "status": "error", "error": "unreadable job metadata"}


def _write_meta(job_id, data, upload_dir=None):
    p = _meta_path(job_id, upload_dir)
    p.write_text(json.dumps(data))


def _recover_if_stale(job_id, job, upload_dir=None, now=None):
    """A restart leaves queued/running jobs with no worker. Mark them failed
    instead of polling forever. Returns the (possibly updated) job."""
    if not job or job.get("status") not in ("queued", "running"):
        return job
    now = now if now is not None else time.time()
    created = float(job.get("created") or 0)
    # From a previous process lifetime, or older than the stale horizon.
    if created < _BOOT_TIME or (now - created) > STALE_AFTER_SECONDS:
        job = dict(job)
        job["status"] = "error"
        job["finished"] = now
        job["error"] = "Worker restarted or timed out; resubmit the job."
        _write_meta(job_id, job, upload_dir)
    return job


def active_count(upload_dir=None):
    n = 0
    d = jobs_dir(upload_dir)
    for p in d.glob("*.json"):
        try:
            job = json.loads(p.read_text())
            job = _recover_if_stale(p.stem, job, upload_dir)
            if job.get("status") in ("queued", "running"):
                n += 1
        except Exception:
            pass
    return n


def create_job(dataset, filename, upload_dir=None):
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id, "dataset": dataset, "filename": filename,
        "status": "queued", "created": time.time(), "finished": None,
        "total": None, "distribution": None, "mean_confidence": None,
        "error": None, "result_csv": None,
    }
    with _LOCK:
        # Atomic admission: count and reserve under one lock so concurrent
        # requests cannot jointly exceed the limit.
        n = 0
        d = jobs_dir(upload_dir)
        for p in d.glob("*.json"):
            try:
                if json.loads(p.read_text()).get("status") in ("queued", "running"):
                    n += 1
            except Exception:
                pass
        if n >= _MAX_CONCURRENT:
            raise RuntimeError(f"Too many active jobs (limit {_MAX_CONCURRENT}). Retry later.")
        _write_meta(job_id, job, upload_dir)
    return job_id


def get_job(job_id, upload_dir=None):
    with _LOCK:
        job = _read_meta(job_id, upload_dir)
        return _recover_if_stale(job_id, job, upload_dir)


def _set(job_id, upload_dir=None, **fields):
    with _LOCK:
        job = _read_meta(job_id, upload_dir)
        if job is None:
            return
        job.update(fields)
        _write_meta(job_id, job, upload_dir)


def run_in_background(fn, job_id, upload_dir=None):
    def _wrap():
        _set(job_id, upload_dir, status="running")
        try:
            summary = fn()
            _set(job_id, upload_dir, status="done", finished=time.time(), **summary)
        except Exception as e:  # noqa: BLE001 — surfaced via job status
            _set(job_id, upload_dir, status="error", finished=time.time(), error=str(e)[:500])
    t = threading.Thread(target=_wrap, daemon=True)
    t.start()
    return t


def public_view(job):
    if not job:
        return None
    view = {k: job.get(k) for k in (
        "job_id", "dataset", "status", "created", "finished",
        "total", "distribution", "mean_confidence", "error")}
    view["has_download"] = bool(job.get("result_csv"))
    return view
