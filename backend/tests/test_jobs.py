"""Background jobs: lifecycle without Flask/TF."""
import sys
import time
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "src.jobs", str(BACKEND / "src" / "jobs.py"))
jobs = importlib.util.module_from_spec(spec)
sys.modules["src.jobs"] = jobs
spec.loader.exec_module(jobs)


def _wait(jid, root, timeout=5):
    deadline = time.time() + timeout
    while jobs.get_job(jid, str(root))["status"] not in ("done", "error") and time.time() < deadline:
        time.sleep(0.05)
    return jobs.public_view(jobs.get_job(jid, str(root)))


def test_lifecycle(tmp_path):
    jdir = jobs.jobs_dir(str(tmp_path))
    assert jdir.exists()
    jid = jobs.create_job("CICIoT2023", ".csv", str(tmp_path))
    assert jobs.public_view(jobs.get_job(jid, str(tmp_path)))["status"] == "queued"

    def _work():
        time.sleep(0.05)
        return {"total": 2, "distribution": {"a": 2}, "mean_confidence": 0.9}

    jobs.run_in_background(_work, jid, str(tmp_path))
    view = _wait(jid, tmp_path)
    assert view["status"] == "done"
    assert view["total"] == 2
    # Metadata persisted to disk: survives process restart.
    assert (tmp_path / "jobs" / f"{jid}.json").exists()
    assert jobs.get_job("nope", str(tmp_path)) is None
    assert jobs.public_view(None) is None


def test_concurrency_bound(tmp_path):
    jobs._MAX_CONCURRENT = 1
    try:
        j1 = jobs.create_job("CICIoT2023", ".csv", str(tmp_path))
        try:
            jobs.create_job("CICIoT2023", ".csv", str(tmp_path))
        except RuntimeError:
            return
        finally:
            pass
        raise AssertionError("second job while one active should be refused")
    finally:
        jobs._MAX_CONCURRENT = 2
