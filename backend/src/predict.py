import logging

import numpy as np
import pandas as pd
import tensorflow as tf

import config
from src.preprocessing import preprocess_features, load_preprocessing_artifacts, transform_with_bundle

log = logging.getLogger(__name__)


class PredictService:
    def __init__(self, dataset="CICIoT2023"):
        self.dataset = dataset
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.class_names = None
        self.input_dim = None
        self._loaded = False

    @property
    def _model_path(self):
        return config.CICIOT2023_MODEL_PATH if self.dataset == "CICIoT2023" else config.NFTONIOTV2_MODEL_PATH

    @property
    def _best_model_path(self):
        return config.CICIOT2023_BEST_PATH if self.dataset == "CICIoT2023" else config.NFTONIOTV2_BEST_PATH

    def load(self):
        if self._loaded:
            return
        # The serving path IS the promoted best-val checkpoint (train.py
        # copies best -> final before evaluating). No silent fallback: a
        # missing final with a stale best present is a failed release.
        from src.release import verify_release
        if self.dataset == "CICIoT2023":
            scaler_path, encoder_path, feature_path = (
                config.CICIOT2023_SCALER, config.CICIOT2023_ENCODER, config.CICIOT2023_FEATURES)
        else:
            scaler_path, encoder_path, feature_path = (
                config.NFTONIOTV2_SCALER, config.NFTONIOTV2_ENCODER, config.NFTONIOTV2_FEATURES)
        model_path = self._model_path
        if not model_path.exists():
            if self._best_model_path.exists():
                raise FileNotFoundError(
                    f"Serving model missing at {model_path} but stale best checkpoint exists. "
                    "Retrain to promote a complete release; refusing to serve a partial run.")
            raise FileNotFoundError(f"Model not found at {self._model_path} for {self.dataset}. Run train.py first.")
        self.manifest = verify_release(
            self.dataset, model_path, scaler_path, encoder_path, feature_path, config.RESULTS_DIR)
        if isinstance(self.manifest, dict) and self.manifest.get("warning"):
            log.warning(f"[{self.dataset}] {self.manifest['warning']}")
        self.model = tf.keras.models.load_model(str(model_path))
        loaded = load_preprocessing_artifacts(self.dataset)
        # Backward compat: old loader returned 3-tuple, new returns 4-tuple.
        if len(loaded) == 4:
            self.scaler, self.label_encoder, self.feature_columns, self.bundle = loaded
        else:
            self.scaler, self.label_encoder, self.feature_columns = loaded
            self.bundle = {"medians": {}, "clip_bounds": {}, "feature_columns": list(self.feature_columns or [])}
        self.class_names = self.label_encoder.classes_
        self.input_dim = self.model.input_shape[1]
        if self.feature_columns is not None and len(self.feature_columns) != self.input_dim:
            raise ValueError(
                f"Artifact mismatch for {self.dataset}: schema has {len(self.feature_columns)} features "
                f"but model expects {self.input_dim}. Retrain to regenerate a consistent release bundle.")
        self._loaded = True
        log.info(f"[{self.dataset}] Model loaded: {self.model.count_params():,} params, {self.input_dim} features, {len(self.class_names)} classes")

    def _transform(self, df):
        # New path: fitted bundle (train-only stats, never refits).
        if self.bundle is not None and self.bundle.get("feature_columns"):
            return transform_with_bundle(df, self.bundle, self.scaler)
        # Legacy fallback for old list-only artifacts.
        X_scaled, _ = preprocess_features(df, fit=False, scaler=self.scaler, feature_columns=self.feature_columns)
        return X_scaled

    def predict(self, df):
        if not self._loaded:
            self.load()
        X_scaled = self._transform(df)
        if X_scaled.shape[1] != self.input_dim:
            raise ValueError(f"Expected {self.input_dim} features, got {X_scaled.shape[1]}.")
        if X_scaled.shape[0] == 0:
            raise ValueError("No valid feature rows after preprocessing.")
        pred_probs = self.model.predict(X_scaled, batch_size=config.BATCH_SIZE, verbose=0)
        pred_indices = np.argmax(pred_probs, axis=1)
        pred_labels = self.class_names[pred_indices]
        pred_confidences = np.max(pred_probs, axis=1)
        results = []
        for i in range(len(X_scaled)):
            top_indices = np.argsort(pred_probs[i])[::-1][:3]
            top_predictions = [{"class": str(self.class_names[idx]), "probability": float(pred_probs[i][idx])} for idx in top_indices]
            results.append({"prediction": str(pred_labels[i]), "confidence": float(pred_confidences[i]), "top_predictions": top_predictions})
        unique, counts = np.unique(pred_labels, return_counts=True)
        distribution = {str(k): int(v) for k, v in zip(unique, counts)}
        return {"results": results, "total": len(results), "distribution": distribution, "mean_confidence": float(np.mean(pred_confidences))}

    def predict_proba(self, df):
        if not self._loaded:
            self.load()
        X_scaled = self._transform(df)
        return self.model.predict(X_scaled, batch_size=config.BATCH_SIZE, verbose=0)

    def predict_single(self, row):
        df = pd.DataFrame([row])
        return self.predict(df)["results"][0]


def get_service(dataset="CICIoT2023"):
    if dataset not in _services:
        _services[dataset] = PredictService(dataset)
    return _services[dataset]


_services = {}
