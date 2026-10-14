"""Flower adapter degrades gracefully without the optional dependency."""
import sys
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402  # pylint: disable=unused-import

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)
sys.modules.setdefault("tensorflow", types.ModuleType("tensorflow"))
stub_model = types.ModuleType("src.model")
stub_model.create_model = lambda *a, **k: None
stub_model.get_client_callbacks = lambda: []
sys.modules.setdefault("src.model", stub_model)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "src.flower_adapter", str(BACKEND / "src" / "flower_adapter.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["src.flower_adapter"] = mod
spec.loader.exec_module(mod)


def test_adapter_importable_without_flower():
    assert isinstance(mod.has_flower(), bool)


def test_adapter_roundtrip_or_actionable_error():
    import numpy as np
    w = [np.ones((2, 2)), np.zeros(2)]
    if mod.has_flower():
        params = mod.to_parameters(w)
        back = mod.from_parameters(params)
        assert len(back) == 2
    else:
        try:
            mod.to_parameters(w)
        except ImportError:
            return
        raise AssertionError("expected ImportError without flwr")
