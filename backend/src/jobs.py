"""Minimal background-job store for large inference files (Phase 3).

Single-replica demo: threads + local files. For multi-worker production
replace with Redis/Celery or equivalent queue with persistence, retries,
and per-user quotas. Jobs are NOT a privacy boundary — same retention and
transport rules as sync predict apply (see docs/DEPLOYMENT.md).
"""
import threading
import time
import uuid
from pathlib import Path

_JOBS: dict = {}
_LOCK = threading.Lock()


def jobs_dir(upload_dir):
    d = Path(upload_dir) / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_job(dataset, filename):
    job_id = uuid.uuid4().hex
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id, "dataset": dataset, "filename": filename,
            "status": "queued", "created": time.time(), "finished": None,
            "total": None, "distribution": None, "mean_confidence": None,
            "error": None, "result_csv": None,
        }
    return job_id


def get_job(job_id):
    with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def _set(job_id, **fields):
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(fields)


def run_in_background(fn, job_id):
    def _wrap():
        _set(job_id, status="running")
        try:
            summary = fn()
            _set(job_id, status="done", finished=time.time(), **summary)
        except Exception as e:  # noqa: BLE001 — surfaced via job status
            _set(job_id, status="error", finished=time.time(), error=str(e)[:500])
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
