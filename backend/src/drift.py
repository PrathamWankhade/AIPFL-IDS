"""Drift check: compare an inference batch against TRAIN statistics (Phase 3).

Uses the fitted bundle (train medians/clip bounds/schema) plus the
StandardScaler train means/scales. Flags features whose batch mean deviates
by more than `threshold` train-stddevs. This is a distribution-shift signal,
not a confirmed-incident detector — route uncertain predictions to
human review instead of auto-blocking.
"""
import numpy as np
import pandas as pd


def drift_report(df, bundle, scaler, threshold=3.0, max_features=10):
    feature_columns = bundle.get("feature_columns") if bundle else None
    if not feature_columns:
        raise ValueError("Preprocessing bundle has no feature schema.")
    means = getattr(scaler, "mean_", None)
    scales = getattr(scaler, "scale_", None)
    if means is None or scales is None:
        raise ValueError("Scaler lacks train mean_/scale_; retrain to regenerate bundle.")

    df = df.copy()
    for col in feature_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(
                [np.inf, -np.inf], np.nan)

    rows = []
    for i, col in enumerate(feature_columns):
        if col not in df.columns:
            rows.append({"feature": col, "status": "missing"})
            continue
        batch_mean = float(np.nanmean(df[col].to_numpy(dtype=np.float64)))
        train_mean = float(means[i])
        train_scale = float(scales[i]) if float(scales[i]) != 0 else 1.0
        z = abs(batch_mean - train_mean) / train_scale if np.isfinite(batch_mean) else float("inf")
        rows.append({"feature": col, "batch_mean": batch_mean,
                     "train_mean": train_mean, "z": float(z),
                     "drifted": bool(z > threshold)})
    rows.sort(key=lambda r: r.get("z", 0), reverse=True)
    drifted = [r for r in rows if r.get("drifted")]
    return {"threshold_z": threshold, "num_features": len(feature_columns),
            "num_drifted": len(drifted),
            "top": rows[:max_features], "drifted": drifted[:max_features]}
