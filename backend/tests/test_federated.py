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
