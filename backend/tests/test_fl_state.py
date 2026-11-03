"""FL resume-state persistence: atomic roundtrip, shape guard, corrupt handling.

train.py is AST-extracted like test_ciciot_loader.py so the suite never
imports TensorFlow.
"""
import ast
import json
import os
import sys
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import config  # noqa: E402

_WANTED = {"fl_state_path", "save_fl_state", "load_fl_state"}


def _load_namespace():
    tree = ast.parse((BACKEND / "train.py").read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if getattr(n, "name", None) in _WANTED]
    found = {getattr(n, "name", None) for n in nodes}
    assert _WANTED <= found, f"train.py missing state helpers: {_WANTED - found}"
    ns = {"np": np, "json": json, "os": os, "config": config}
    exec(compile(ast.Module(body=nodes, type_ignores=[]),
                 str(BACKEND / "train.py"), "exec"), ns)
    return ns


NS = _load_namespace()


class _Model:
    def __init__(self, weights):
        self._w = [np.array(w) for w in weights]

    def get_weights(self):
        return [np.array(w) for w in self._w]

    def set_weights(self, ws):
        self._w = [np.array(w) for w in ws]


def test_state_roundtrip(tmp_path):
    path = tmp_path / "fl_state_X.npz"
    weights = [np.random.default_rng(0).normal(size=(3, 4)).astype(np.float32),
               np.arange(7, dtype=np.float32)]
    history = {"val_accuracy": [0.7, 0.9], "participating_clients": [2, 2]}

    NS["save_fl_state"](path, 12, weights, history, 0.9045)
    assert path.exists()
    # No stray temp file left behind (atomic replace).
    assert not list(tmp_path.glob("*.tmp"))

    model = _Model([np.zeros((3, 4), np.float32), np.zeros(7, np.float32)])
    loaded = NS["load_fl_state"](path, model)
    assert loaded is not None
    round_num, hist, best = loaded
    assert round_num == 12
    assert hist == history
    assert best == 0.9045
    for got, want in zip(model.get_weights(), weights):
        np.testing.assert_array_equal(got, want)


def test_state_shape_mismatch_returns_none(tmp_path):
    path = tmp_path / "fl_state_X.npz"
    NS["save_fl_state"](path, 3, [np.zeros((5, 5))], {}, 0.5)
    # Model with different architecture -> refuse, don't load garbage.
    assert NS["load_fl_state"](path, _Model([np.zeros((2, 2))])) is None
    # Even same count but different shapes -> refuse.
    assert NS["load_fl_state"](path, _Model([np.zeros((5, 5)), np.zeros(2)])) is None


def test_missing_and_corrupt_state_return_none(tmp_path):
    assert NS["load_fl_state"](tmp_path / "nope.npz", _Model([np.zeros(2)])) is None
    bad = tmp_path / "fl_state_bad.npz"
    bad.write_bytes(b"not an npz at all")
    assert NS["load_fl_state"](bad, _Model([np.zeros(2)])) is None
