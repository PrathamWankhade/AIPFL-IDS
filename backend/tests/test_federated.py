"""Phase 0: FedAvg validation + train/val/test split contract."""
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
sys.modules["src"] = PKG
sys.modules["tensorflow"] = types.ModuleType("tensorflow")
stub_model = types.ModuleType("src.model")
stub_model.create_model = lambda *a, **k: None
stub_model.get_client_callbacks = lambda: []
sys.modules["src.model"] = stub_model

spec = importlib.util.spec_from_file_location(
    "src.federated", str(BACKEND / "src" / "federated.py"))
fed = importlib.util.module_from_spec(spec)
sys.modules["src.federated"] = fed
spec.loader.exec_module(fed)


def test_weighted_average_math():
    w1 = [np.ones((2, 2)), np.zeros(2)]
    w2 = [np.ones((2, 2)) * 3, np.ones(2)]
    out = fed.weighted_fed_average([w1, w2], [1, 3])
    assert abs(out[0][0, 0] - 2.5) < 1e-9


def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def test_weighted_average_rejects_bad_inputs():
    w1 = [np.ones((2, 2))]
    assert _raises(lambda: fed.weighted_fed_average([], []))
    assert _raises(lambda: fed.weighted_fed_average([w1], [0]))
    assert _raises(lambda: fed.weighted_fed_average([w1, [np.ones((9,))]], [1, 1]))
    assert _raises(lambda: fed.weighted_fed_average([[np.full((2, 2), np.nan)]], [1]))
    assert _raises(lambda: fed.weighted_fed_average([[np.full((2, 2), np.inf)]], [1]))


def test_split_contract_documented():
    # Contract: train/val/test from raw-first split; test never in loop.
    # Enforced by train.py using VALIDATION_SPLIT + X_val in federated_training_loop.
    assert config.VALIDATION_SPLIT > 0 and config.TEST_SPLIT > 0
    assert config.VALIDATION_SPLIT + config.TEST_SPLIT < 1.0
    import inspect
    sig = inspect.signature(fed.federated_training_loop)
    assert "X_val" in sig.parameters and "y_val" in sig.parameters


def test_partial_participation_contract():
    import inspect
    sig = inspect.signature(fed.federated_training_loop)
    assert "client_fraction" in sig.parameters and "min_clients" in sig.parameters
    assert 0.0 < config.CLIENT_FRACTION <= 1.0
    assert config.MIN_CLIENTS >= 1


def test_delta_norm_guard():
    import numpy as np
    g = [np.zeros((2, 2)), np.zeros(2)]
    small = [np.full((2, 2), 0.1), np.full(2, 0.1)]
    assert fed.update_delta_norm(small, g) < 1.0
    assert fed.validate_client_update(small, g, max_norm=10.0) < 10.0
    big = [np.full((2, 2), 100.0), np.zeros(2)]
    try:
        fed.validate_client_update(big, g, max_norm=10.0)
    except ValueError:
        return
    raise AssertionError("over-norm delta should be rejected")


# ── Resume: a restarted run must reproduce an uninterrupted one exactly ──

class _StubModel:
    def __init__(self, weights):
        self._w = [np.array(w) for w in weights]
        self.saved = []

    def get_weights(self):
        return [np.array(w) for w in self._w]

    def set_weights(self, ws):
        self._w = [np.array(w) for w in ws]

    def evaluate(self, X, y, batch_size=None, verbose=0):
        m = float(np.mean(self._w[0]))
        return abs(m), min(1.0, 0.5 + m)  # deterministic given weights

    def save(self, path):
        self.saved.append(str(path))


def _deterministic_train_client(global_weights, X_client, y_client, input_dim,
                                num_classes, class_weight=None):
    w0 = np.asarray(global_weights[0], dtype=np.float64)
    delta = 0.05 * float(np.mean(X_client)) + 0.01 * len(X_client) / 100.0
    return {"weights": [w0 + delta], "loss": 0.5, "accuracy": 0.5,
            "samples": int(len(X_client)), "delta_norm": abs(delta)}


def _build_clients():
    rng = np.random.default_rng(0)
    sizes = [50, 80, 120]
    clients = []
    for s in sizes:
        X = rng.normal(size=(s, 4))
        y = rng.integers(0, 3, size=s)
        clients.append((X, y))
    return clients, sizes


def _run(tmp_path, clients, sizes, start_round=1, initial_history=None,
         initial_best=0.0, rounds=3, seed=123, capture=None):
    X_val = np.zeros((10, 4))
    y_val = np.zeros(10, dtype=int)
    model = _StubModel([np.zeros(4)])

    def cb(round_num, weights, hist, best):
        if capture is not None:
            capture["round"] = round_num
            capture["weights"] = [np.array(w) for w in weights]
            capture["history"] = {k: list(v) for k, v in hist.items()}
            capture["best"] = best

    return fed.federated_training_loop(
        model, clients, sizes, X_val, y_val, 4, 3,
        global_rounds=rounds, verbose=False,
        best_model_path=str(tmp_path / "best.keras"),
        final_model_path=str(tmp_path / "final.keras"),
        client_fraction=0.67, seed=seed, start_round=start_round,
        initial_history=initial_history, initial_best_accuracy=initial_best,
        state_callback=cb)


def test_state_callback_fires_once_per_round(tmp_path, monkeypatch):
    monkeypatch.setattr(fed, "train_client", _deterministic_train_client)
    clients, sizes = _build_clients()
    seen = []

    def cb(r, w, h, b):
        seen.append(r)

    X_val = np.zeros((10, 4))
    y_val = np.zeros(10, dtype=int)
    fed.federated_training_loop(
        _StubModel([np.zeros(4)]), clients, sizes, X_val, y_val, 4, 3,
        global_rounds=4, verbose=False,
        best_model_path=str(tmp_path / "b.keras"),
        final_model_path=str(tmp_path / "f.keras"),
        client_fraction=0.67, seed=7, state_callback=cb)
    assert seen == [1, 2, 3, 4]


def test_resume_reproduces_uninterrupted_run(tmp_path, monkeypatch):
    """RNG replay must make resumed history bit-identical to a full run."""
    monkeypatch.setattr(fed, "train_client", _deterministic_train_client)
    clients, sizes = _build_clients()

    # Full 3-round run.
    full = _run(tmp_path, clients, sizes, rounds=3)

    # First 2 rounds, capturing end-of-round-2 state.
    cap = {}
    part1 = _run(tmp_path, clients, sizes, rounds=2, capture=cap)
    assert cap["round"] == 2

    # Resume from round 3 with restored weights/history/best.
    resumed_model = _StubModel(cap["weights"])
    X_val = np.zeros((10, 4))
    y_val = np.zeros(10, dtype=int)
    resumed = fed.federated_training_loop(
        resumed_model, clients, sizes, X_val, y_val, 4, 3,
        global_rounds=3, verbose=False,
        best_model_path=str(tmp_path / "best.keras"),
        final_model_path=str(tmp_path / "final.keras"),
        client_fraction=0.67, seed=123, start_round=3,
        initial_history=part1["history"],
        initial_best_accuracy=part1["best_accuracy"])

    # History (incl. participation + comm bytes) matches the full run exactly.
    assert resumed["history"] == full["history"]
    assert resumed["best_accuracy"] == full["best_accuracy"]
    # Participation was actually partial (rng replay is doing real work).
    assert all(p < len(clients) for p in full["history"]["participating_clients"])
