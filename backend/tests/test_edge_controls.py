"""Edge controls: API key gate + per-IP rate limiter (unit-level)."""
import importlib.util
import sys
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)
sys.modules.setdefault("tensorflow", types.ModuleType("tensorflow"))
stub_predict = types.ModuleType("src.predict")
stub_predict.get_service = lambda ds="CICIoT2023": None
sys.modules["src.predict"] = stub_predict
try:
    import flask_cors  # noqa: F401
except ImportError:
    fake_cors = types.ModuleType("flask_cors")
    fake_cors.CORS = lambda *a, **k: None
    sys.modules["flask_cors"] = fake_cors

spec = importlib.util.spec_from_file_location(
    "server_app_edge", str(BACKEND / "server" / "app.py"))
appmod = importlib.util.module_from_spec(spec)
sys.modules["server_app_edge"] = appmod
spec.loader.exec_module(appmod)


def test_api_key_open_by_default(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", None)
    assert appmod.is_api_key_ok(None) is True
    assert appmod.is_api_key_ok("anything") is True


def test_api_key_enforced_when_set(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret")
    assert appmod.is_api_key_ok(None) is False
    assert appmod.is_api_key_ok("wrong") is False
    assert appmod.is_api_key_ok("secret") is True


def test_rate_limiter_blocks_over_quota():
    rl = appmod.RateLimiter(per_minute=2)
    assert rl.allowed("ip", now=1000.0) is True
    assert rl.allowed("ip", now=1001.0) is True
    assert rl.allowed("ip", now=1002.0) is False
    assert rl.allowed("ip", now=1063.0) is True  # window slid


def test_client_ip_ignores_forwarded_by_default(monkeypatch):
    monkeypatch.setattr(config, "TRUST_PROXY", False)
    with appmod.app.test_request_context(
            "/", headers={"X-Forwarded-For": "9.9.9.9"},
            environ_base={"REMOTE_ADDR": "1.2.3.4"}):
        assert appmod.client_ip() == "1.2.3.4"


def test_client_ip_trusts_proxy_when_enabled(monkeypatch):
    monkeypatch.setattr(config, "TRUST_PROXY", True)
    with appmod.app.test_request_context(
            "/", headers={"X-Forwarded-For": "9.9.9.9, 8.8.8.8"},
            environ_base={"REMOTE_ADDR": "1.2.3.4"}):
        assert appmod.client_ip() == "9.9.9.9"
