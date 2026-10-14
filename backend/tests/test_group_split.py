"""Capture-aware split: no group spans train/val/test."""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def test_group_holdout_no_overlap():
    n = 90
    df = pd.DataFrame({
        "f": np.random.default_rng(0).normal(size=n),
        "label": ["a", "b", "c"] * 30,
        "capture": [f"cap{i // 9}" for i in range(n)],
    })
    X, y = df[["f"]], df["label"].astype(str)
    groups = df["capture"].to_numpy()
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(X, y, groups))
    assert not set(groups[tr]) & set(groups[te])
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr2, va = next(gss2.split(X.iloc[tr], y.iloc[tr], groups[tr]))
    assert not set(groups[tr][tr2]) & set(groups[tr][va])
