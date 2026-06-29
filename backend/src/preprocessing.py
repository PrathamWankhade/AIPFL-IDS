import joblib
import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler, LabelEncoder

import config


def remove_unstable_features(df):
    cols_to_drop = [c for c in config.UNSTABLE_FEATURES if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df


def remove_constant_features(df):
    selector = VarianceThreshold(threshold=0.0)
    selector.fit(df.select_dtypes(include=[np.number]))
    constant_cols = df.select_dtypes(include=[np.number]).columns[~selector.get_support()].tolist()
    if constant_cols:
        df = df.drop(columns=constant_cols)
    return df


def preprocess_features(X, fit=False, scaler=None):
    if isinstance(X, pd.DataFrame):
        X = remove_unstable_features(X)
        X = remove_constant_features(X)
        X = X.select_dtypes(include=[np.number])

    if fit:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        assert scaler is not None, "scaler must be provided for inference"
        X_scaled = scaler.transform(X)

    return X_scaled, scaler


def encode_labels(y, fit=False, label_encoder=None):
    if fit:
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
    else:
        assert label_encoder is not None, "label_encoder must be provided for inference"
        y_encoded = label_encoder.transform(y)
    return y_encoded, label_encoder


def save_preprocessing_artifacts(scaler, label_encoder):
    joblib.dump(scaler, config.SCALER_PATH)
    joblib.dump(label_encoder, config.LABEL_ENCODER_PATH)


def load_preprocessing_artifacts():
    scaler = joblib.load(config.SCALER_PATH)
    label_encoder = joblib.load(config.LABEL_ENCODER_PATH)
    return scaler, label_encoder
