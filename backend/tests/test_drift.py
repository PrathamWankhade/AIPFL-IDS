"""Drift report: flags shifted batches, ignores clean ones."""
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)

import importlib.util


def _load(name):
    spec = importlib.util.spec_from_file_location(
        f"src.{name}", str(BACKEND / "src" / f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"src.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_drift_flags_shift():
    pre = _load("preprocessing")
    drift = _load("drift")
    train = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                          "b": [10.0, 11.0, 9.0, 10.5, 10.0, 9.5]})
    _, bundle, scaler = pre.fit_preprocessor(train)
    clean = pd.DataFrame({"a": [2.0, 3.0, 4.0], "b": [10.0, 10.0, 10.0]})
    assert drift.drift_report(clean, bundle, scaler)["num_drifted"] == 0
    shifted = pd.DataFrame({"a": [100.0, 101.0, 99.0], "b": [10.0, 10.0, 10.0]})
    rep = drift.drift_report(shifted, bundle, scaler)
    assert rep["num_drifted"] >= 1
    assert rep["top"][0]["feature"] == "a"
