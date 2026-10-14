"""Phase 0: preprocessing must never refit on inference payloads."""
import importlib.util
import sys
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules["src"] = PKG


def load_pre():
    spec = importlib.util.spec_from_file_location(
        "src.preprocessing", str(BACKEND / "src" / "preprocessing.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["src.preprocessing"] = mod
    spec.loader.exec_module(mod)
    return mod


pre = load_pre()
pd = __import__("pandas")
np = __import__("numpy")


def test_single_row_and_column_permutation():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [5.0, 5.0, 5.0, 5.0]})
    _, bundle, scaler = pre.fit_preprocessor(df)
    assert bundle["feature_columns"] == ["a"]  # constant 'b' removed at fit
    one = pd.DataFrame({"b": [5.0], "a": [2.5]})  # permuted + single row
    out = pre.transform_with_bundle(one, bundle, scaler)
    assert out.shape == (1, 1)


def test_missing_column_raises():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [1.0, 2.0, 3.0]})
    _, bundle, scaler = pre.fit_preprocessor(df)
    try:
        pre.transform_with_bundle(pd.DataFrame({"b": [1.0]}), bundle, scaler)
    except ValueError:
        return
    raise AssertionError("missing required column should raise")


def test_inf_imputed_with_train_median():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})
    _, bundle, scaler = pre.fit_preprocessor(df)
    out = pre.transform_with_bundle(pd.DataFrame({"a": [float("inf")]}), bundle, scaler)
    assert np.all(np.isfinite(out))
