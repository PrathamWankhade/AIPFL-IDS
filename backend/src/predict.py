import logging

import numpy as np
import pandas as pd
import tensorflow as tf

import config
from src.preprocessing import preprocess_features, load_preprocessing_artifacts

log = logging.getLogger(__name__)


class PredictService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.class_names = None
        self.input_dim = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        if not config.MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {config.MODEL_PATH}. Run train.py first.")
        self.model = tf.keras.models.load_model(str(config.MODEL_PATH))
        self.scaler, self.label_encoder = load_preprocessing_artifacts()
        self.class_names = self.label_encoder.classes_
        self.input_dim = self.model.input_shape[1]
        self._loaded = True
        log.info(f"Model loaded: {self.model.count_params():,} params, {self.input_dim} features, {len(self.class_names)} classes")

    def predict(self, df):
        if not self._loaded:
            self.load()
        X_scaled, _ = preprocess_features(df, fit=False, scaler=self.scaler)
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
        X_scaled, _ = preprocess_features(df, fit=False, scaler=self.scaler)
        return self.model.predict(X_scaled, batch_size=config.BATCH_SIZE, verbose=0)

    def predict_single(self, row):
        df = pd.DataFrame([row])
        return self.predict(df)["results"][0]


predict_service = PredictService()
