"""Tests for the centralized baseline harness (no TensorFlow import)."""

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Stub the `src` package (same pattern as the other suites) so importing
# `src.evaluation` / `src.splits` never executes src/__init__.py -> TensorFlow.
PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)

import baselines  # noqa: E402


CLASSES = ["benign", "ddos", "recon"]


def _toy_data(n=300, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, len(CLASSES), size=n)
    X = rng.normal(size=(n, 6)) + y[:, None]  # separable-ish
    return X.astype(np.float64), y.astype(int)


def test_run_baseline_reports_measured_metrics_only():
    X, y = _toy_data()
    X_tr, y_tr = X[:240], y[:240]
    X_te, y_te = X[240:], y[240:]

    metrics, est = baselines.run_baseline(
        "rf", X_tr, y_tr, X_te, y_te, CLASSES, seed=7, n_estimators=10)

    for key in ("test_accuracy", "macro_f1", "balanced_accuracy",
                "per_class", "fit_seconds", "n_train", "n_test", "seed"):
        assert key in metrics
    assert 0.0 <= metrics["test_accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert set(metrics["per_class"]) == set(CLASSES)
    # RF exposes probabilities, so ECE must be a real number, not a claim.
    assert metrics["ece"] is not None and 0.0 <= metrics["ece"] <= 1.0
    assert metrics["n_train"] == 240 and metrics["n_test"] == 60
    assert metrics["seed"] == 7
    assert est is not None


def test_run_baseline_rejects_unknown_model():
    X, y = _toy_data(n=60)
    with pytest.raises(ValueError, match="rf"):
        baselines.run_baseline("xgboost", X[:40], y[:40], X[40:], y[40:], CLASSES)


def test_logreg_baseline_runs_and_returns_finite_metrics():
    X, y = _toy_data(n=200, seed=3)
    metrics, _ = baselines.run_baseline(
        "logreg", X[:150], y[:150], X[150:], y[150:], CLASSES, seed=1)
    assert np.isfinite(metrics["test_accuracy"])
    assert np.isfinite(metrics["macro_f1"])
    assert metrics["fit_seconds"] >= 0.0


def test_split_is_deterministic_and_disjoint():
    """Same seed -> identical rows; train/val/test never overlap."""
    from src.splits import stratified_splits
    import config

    rng = np.random.default_rng(0)
    X_raw = pd.DataFrame(rng.normal(size=(400, 4)), columns=list("abcd"))
    y_raw = pd.Series(rng.integers(0, 2, size=400))

    a = stratified_splits(X_raw, y_raw, seed=11)
    b = stratified_splits(X_raw, y_raw, seed=11)
    for fa, fb in zip(a, b):
        assert fa.reset_index(drop=True).equals(fb.reset_index(drop=True))

    X_tr, X_va, X_te, y_tr, y_va, y_te = a
    assert len(X_tr) + len(X_va) + len(X_te) == 400
    assert set(X_tr.index) & set(X_te.index) == set()
    assert set(X_tr.index) & set(X_va.index) == set()
    assert set(X_va.index) & set(X_te.index) == set()
    # test split honours TEST_SPLIT
    assert abs(len(X_te) / 400 - config.TEST_SPLIT) < 0.02
