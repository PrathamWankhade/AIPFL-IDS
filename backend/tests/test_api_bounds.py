"""Upload bounds enforced during parsing (not after full load)."""
import importlib.util
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
    "server_app_bounds", str(BACKEND / "server" / "app.py"))
appmod = importlib.util.module_from_spec(spec)
sys.modules["server_app_bounds"] = appmod
spec.loader.exec_module(appmod)


def test_csv_row_cap_enforced_while_streaming(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 3)
    p = tmp_path / "big.csv"
    pd.DataFrame({"a": [1, 2, 3, 4, 5]}).to_csv(p, index=False)
    try:
        appmod.load_file_data(str(p))
    except ValueError as e:
        assert "rows" in str(e).lower()
        return
    raise AssertionError("oversize CSV must be rejected")


def test_csv_column_cap_checked_before_body(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_COLUMNS", 2)
    p = tmp_path / "wide.csv"
    pd.DataFrame({"a": [1], "b": [2], "c": [3]}).to_csv(p, index=False)
    try:
        appmod.load_file_data(str(p))
    except ValueError as e:
        assert "columns" in str(e).lower()
        return
    raise AssertionError("over-wide CSV must be rejected")


def test_parquet_metadata_checked_first(tmp_path, monkeypatch):
    pytest = __import__("pytest")
    pq = pytest.importorskip("pyarrow.parquet")
    monkeypatch.setattr(config, "MAX_UPLOAD_ROWS", 2)
    p = tmp_path / "big.parquet"
    pd.DataFrame({"a": [1, 2, 3]}).to_parquet(p, index=False)
    try:
        appmod.load_file_data(str(p))
    except ValueError as e:
        assert "rows" in str(e).lower()
        return
    raise AssertionError("oversize parquet must be rejected from metadata")
