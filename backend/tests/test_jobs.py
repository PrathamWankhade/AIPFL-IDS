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


def test_lifecycle(tmp_path):
    jdir = jobs.jobs_dir(str(tmp_path))
    assert jdir.exists()
    jid = jobs.create_job("CICIoT2023", ".csv")
    assert jobs.public_view(jobs.get_job(jid))["status"] == "queued"

    def _work():
        time.sleep(0.05)
        return {"total": 2, "distribution": {"a": 2}, "mean_confidence": 0.9}

    jobs.run_in_background(_work, jid)
    deadline = time.time() + 5
    while jobs.get_job(jid)["status"] not in ("done", "error") and time.time() < deadline:
        time.sleep(0.05)
    view = jobs.public_view(jobs.get_job(jid))
    assert view["status"] == "done"
    assert view["total"] == 2
    assert jobs.get_job("nope") is None
    assert jobs.public_view(None) is None
