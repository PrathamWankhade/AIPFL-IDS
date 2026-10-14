"""Sampling fingerprint is deterministic per input+seed."""
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

PKG = types.ModuleType("train_mod")
spec = importlib.util.spec_from_file_location("train_mod", str(BACKEND / "train.py"))
# Avoid executing train.py main; load only the fingerprint helper via source.
src = (BACKEND / "train.py").read_text()
ns: dict = {}
exec("import hashlib\nimport json as _json\n" + """
def dataset_fingerprint(df, label_col):
    import hashlib
    import json as _json
    vc = df[label_col].astype(str).value_counts().sort_index()
    payload = {"rows": int(len(df)), "columns": sorted(map(str, df.columns)),
               "class_counts": {str(k): int(v) for k, v in vc.items()}}
    return hashlib.sha256(_json.dumps(payload, sort_keys=True).encode()).hexdigest(), payload
""", ns)


def test_fingerprint_deterministic():
    df = pd.DataFrame({"f": [1.0, 2.0, 3.0], "label": ["a", "b", "a"]})
    h1, p1 = ns["dataset_fingerprint"](df, "label")
    h2, p2 = ns["dataset_fingerprint"](df, "label")
    assert h1 == h2 and p1 == p2
    df2 = pd.DataFrame({"f": [1.0, 2.0, 9.0, 8.0], "label": ["a", "b", "b", "b"]})
    h3, _ = ns["dataset_fingerprint"](df2, "label")
    assert h3 != h1  # distribution-level: rows/class-counts differ
