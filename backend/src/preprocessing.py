import joblib
import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler, LabelEncoder

import config


def clean_infinite(df):
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return df
    df[numeric.columns] = numeric.replace([np.inf, -np.inf], np.nan)
    for col in numeric.columns:
        if df[col].isna().any():
            med = df[col].median()
            if pd.isna(med):
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna(med)
    return df


def clip_extreme(df, threshold=1e15):
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return df
    for col in numeric.columns:
        col_max = numeric[col].max()
        col_min = numeric[col].min()
        if col_max > threshold or col_min < -threshold:
            qlo, qhi = numeric[col].quantile([0.01, 0.99])
            iqr = qhi - qlo
            if iqr == 0:
                df[col] = df[col].clip(qlo, qhi)
            else:
                lower = qlo - 3 * iqr
                upper = qhi + 3 * iqr
                df[col] = df[col].clip(lower, upper)
    return df


def remove_constant_features(df):
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty or len(df) < 2:
        return df
    selector = VarianceThreshold(threshold=0.0)
    selector.fit(numeric)
    constant_cols = numeric.columns[~selector.get_support()].tolist()
    if constant_cols:
        df = df.drop(columns=constant_cols)
    return df


# ── Fitted preprocessing bundle (Phase 0 fix) ──────────────────────
# Inference must NEVER call fit(). All statistics are computed on the
# training split only and reused verbatim for validation/test/inference.

def fit_preprocessor(df_features, threshold=1e15):
    """Fit imputation/clipping/selection/scaling on TRAINING rows only.

    Returns (X_scaled, bundle) where bundle holds everything needed to
    transform future data deterministically without refitting.
    """
    df = df_features.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # 1. Infinite -> NaN, then train medians (0 if column all-NaN).
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    medians = {}
    for col in numeric_cols:
        med = df[col].median()
        medians[col] = float(0.0) if pd.isna(med) else float(med)
        df[col] = df[col].fillna(medians[col])

    # 2. Train clipping bounds for extreme columns only.
    clip_bounds = {}
    for col in numeric_cols:
        col_max = float(df[col].max())
        col_min = float(df[col].min())
        if col_max > threshold or col_min < -threshold:
            qlo, qhi = df[col].quantile([0.01, 0.99])
            qlo, qhi = float(qlo), float(qhi)
            iqr = qhi - qlo
            if iqr == 0:
                lower, upper = qlo, qhi
            else:
                lower, upper = qlo - 3 * iqr, qhi + 3 * iqr
            clip_bounds[col] = (float(lower), float(upper))
            df[col] = df[col].clip(lower, upper)

    # 3. Constant-feature selection fit on train only.
    numeric = df.select_dtypes(include=[np.number])
    feature_columns = numeric.columns.tolist()
    if len(df) >= 2 and not numeric.empty:
        selector = VarianceThreshold(threshold=0.0)
        selector.fit(numeric)
        kept = numeric.columns[selector.get_support()].tolist()
        if kept:
            feature_columns = kept
        df = df[feature_columns]

    # 4. Scaler fit on train only.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_columns].to_numpy(dtype=np.float64))

    bundle = {
        "medians": medians,
        "clip_bounds": {k: [float(v[0]), float(v[1])] for k, v in clip_bounds.items()},
        "feature_columns": list(feature_columns),
        "threshold": float(threshold),
    }
    return X_scaled, bundle, scaler


def transform_with_bundle(df_features, bundle, scaler):
    """Transform new data with a fitted bundle. Never fits; raises on bad schema."""
    if bundle is None or scaler is None:
        raise ValueError("Preprocessing bundle/scaler is missing.")
    feature_columns = bundle.get("feature_columns")
    if not feature_columns:
        raise ValueError("Preprocessing bundle has no feature schema.")
    medians = bundle.get("medians", {})
    clip_bounds = bundle.get("clip_bounds", {})

    df = df_features.copy()

    # Extra columns are ignored (documented policy); missing required
    # numeric columns are zero-filled only if they were constant-imputed
    # at train time — otherwise raise an actionable error.
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature column(s): {missing[:10]}")

    # Impute with TRAIN medians; reject non-finite-after-imputation.
    for col in feature_columns:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            s = s.replace([np.inf, -np.inf], np.nan)
            if s.isna().any():
                s = s.fillna(medians.get(col, 0.0))
            df[col] = s
    # Clip with TRAIN bounds.
    for col, bounds in clip_bounds.items():
        if col in df.columns:
            df[col] = df[col].clip(bounds[0], bounds[1])

    X = df[feature_columns].to_numpy(dtype=np.float64)
    if X.shape[0] == 0:
        raise ValueError("No valid feature rows after preprocessing.")
    if not np.all(np.isfinite(X)):
        raise ValueError("Non-finite values remain after preprocessing; check input numbers.")
    return scaler.transform(X)


def preprocess_features(X, fit=False, scaler=None, feature_columns=None):
    if isinstance(X, pd.DataFrame):
        X = clean_infinite(X)
        X = clip_extreme(X)
        if fit:
            X = remove_constant_features(X)
        X = X.select_dtypes(include=[np.number])
        if feature_columns is not None:
            missing = set(feature_columns) - set(X.columns)
            if missing:
                for c in missing:
                    X[c] = 0
            X = X[feature_columns]
    if fit:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        assert scaler is not None
        X_scaled = scaler.transform(X)
    return X_scaled, scaler


def encode_labels(y, fit=False, label_encoder=None):
    if fit:
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
    else:
        assert label_encoder is not None
        y_encoded = label_encoder.transform(y)
    return y_encoded, label_encoder


def save_preprocessing_artifacts(scaler, label_encoder, scaler_path=None, encoder_path=None, feature_path=None, feature_columns=None, bundle=None):
    joblib.dump(scaler, scaler_path or config.CICIOT2023_SCALER)
    joblib.dump(label_encoder, encoder_path or config.CICIOT2023_ENCODER)
    if feature_path:
        # New format: full bundle dict (ordered schema + train stats).
        # Old format was a plain list; loaders accept both.
        payload = bundle if bundle is not None else feature_columns
        if bundle is not None and feature_columns is not None:
            payload = dict(bundle)
            payload["feature_columns"] = list(feature_columns)
        joblib.dump(payload, feature_path)


def load_preprocessing_artifacts(dataset="CICIoT2023"):
    if dataset == "NF-ToN-IoT-V2":
        scaler = joblib.load(config.NFTONIOTV2_SCALER)
        label_encoder = joblib.load(config.NFTONIOTV2_ENCODER)
        feature_path = config.NFTONIOTV2_FEATURES
    else:
        scaler = joblib.load(config.CICIOT2023_SCALER)
        label_encoder = joblib.load(config.CICIOT2023_ENCODER)
        feature_path = config.CICIOT2023_FEATURES
    feature_columns = None
    bundle = None
    if feature_path.exists():
        payload = joblib.load(feature_path)
        if isinstance(payload, dict) and "feature_columns" in payload:
            bundle = payload
            feature_columns = payload["feature_columns"]
        else:
            # Backward compat: old artifact stored only the column list.
            feature_columns = payload
            bundle = {"medians": {}, "clip_bounds": {}, "feature_columns": list(feature_columns)}
    return scaler, label_encoder, feature_columns, bundle
