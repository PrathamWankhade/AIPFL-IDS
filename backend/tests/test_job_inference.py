"""Streaming job inference: chunked, bounded, aggregated (no TF)."""
import sys
import types
from pathlib import Path

import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "src.job_inference", str(BACKEND / "src" / "job_inference.py"))
ji = importlib.util.module_from_spec(spec)
sys.modules["src.job_inference"] = ji
spec.loader.exec_module(ji)


class StubSvc:
    def predict(self, df):
        n = len(df)
        return {"results": [{"prediction": "Benign", "confidence": 0.8}] * n,
                "total": n, "distribution": {"Benign": n}, "mean_confidence": 0.8}


def test_streaming_csv_above_sync_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 3)  # sync would reject
    p = tmp_path / "big.csv"
    pd.DataFrame({"a": [1, 2, 3, 4, 5]}).to_csv(p, index=False)
    out_csv = tmp_path / "out.csv"
    summary = ji.run_job_file(StubSvc(), str(p), ".csv", str(out_csv),
                              max_rows=100, chunk_rows=2)
    assert summary["total"] == 5
    assert summary["distribution"] == {"Benign": 5}
    assert abs(summary["mean_confidence"] - 0.8) < 1e-9
    lines = out_csv.read_text().strip().splitlines()
    assert len(lines) == 6  # header + 5 rows


def test_streaming_respects_job_cap(tmp_path):
    p = tmp_path / "big.csv"
    pd.DataFrame({"a": [1, 2, 3, 4, 5]}).to_csv(p, index=False)
    try:
        ji.run_job_file(StubSvc(), str(p), ".csv", str(tmp_path / "o.csv"),
                        max_rows=4, chunk_rows=2)
    except ValueError as e:
        assert "exceeds" in str(e).lower()
        return
    raise AssertionError("over-cap job file must be rejected")


def test_streaming_parquet(tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("pyarrow")
    p = tmp_path / "f.parquet"
    pd.DataFrame({"a": [1.0, 2.0, 3.0]}).to_parquet(p, index=False)
    summary = ji.run_job_file(StubSvc(), str(p), ".parquet",
                              str(tmp_path / "o.csv"), max_rows=100)
    assert summary["total"] == 3
