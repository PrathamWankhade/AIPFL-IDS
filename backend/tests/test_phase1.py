"""Phase 1: metrics + non-IID partitions (no TF required)."""
import importlib.util
import sys
import types
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)
sys.modules.setdefault("tensorflow", types.ModuleType("tensorflow"))
stub_model = types.ModuleType("src.model")
stub_model.create_model = lambda *a, **k: None
stub_model.get_client_callbacks = lambda: []
sys.modules["src.model"] = stub_model


def _load(name):
    spec = importlib.util.spec_from_file_location(
        f"src.{name}", str(BACKEND / "src" / f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"src.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_non_iid_partitions_differ():
    fed = _load("federated")
    rng = np.random.default_rng(0)
    X = rng.normal(size=(600, 4))
    y = np.array([i % 3 for i in range(600)])
    iid_clients, _ = fed.create_clients(X, y, num_clients=3, partition="iid", seed=0)
    skew_clients, skew_sizes = fed.create_clients(
        X, y, num_clients=3, partition="label_skew", alpha=0.2, seed=0)
    assert all(s > 0 for s in skew_sizes)
    hist = fed.client_label_histogram([c[1] for c in skew_clients], num_classes=3)
    assert len(hist) == 3
    # skew should produce uneven prevalence vs roughly-even IID
    iid_hist = fed.client_label_histogram([c[1] for c in iid_clients], num_classes=3)
    assert hist != iid_hist


def test_evaluation_metrics():
    ev = _load("evaluation")
    n, k = 120, 3
    rng = np.random.default_rng(1)
    y = rng.integers(0, k, size=n)
    probs = np.full((n, k), 0.1)
    probs[np.arange(n), y] = 0.8
    probs /= probs.sum(axis=1, keepdims=True)

    class Stub:
        def evaluate(self, X, yt, batch_size=None, verbose=0):
            return 0.5, 0.8

        def predict(self, X, batch_size=None, verbose=0):
            return probs

    out = ev.evaluate_model(Stub(), np.zeros((n, 4)), y,
                            ["a", "b", "c"], history=None,
                            save_dir=Path("C:/Users/prath/AppData/Local/Temp/opencode"))
    assert 0.0 <= out["macro_f1"] <= 1.0
    assert 0.0 <= out["ece"] <= 1.0
    assert len(out["per_class"]) == 3
    assert out["benign_fpr"] is None  # no benign class here
    ece_bad = ev.expected_calibration_error(
        np.ones(n, dtype=int), np.tile([0.99, 0.005, 0.005], (n, 1)))
    assert ece_bad > 0.9  # overconfident wrong predictions -> high ECE
