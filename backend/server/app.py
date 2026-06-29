import os
import sys
import uuid
import time
import logging
import threading
from functools import wraps

import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.predict import predict_service
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "https://*.vercel.app"], supports_credentials=True)

ALLOWED_EXTENSIONS = {".csv", ".parquet"}
MAX_CONTENT_LENGTH = config.MAX_FILE_SIZE_MB * 1024 * 1024


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def load_file_data(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return pd.read_csv(filepath)
    elif ext == ".parquet":
        return pd.read_parquet(filepath)
    raise ValueError(f"Unsupported file type: {ext}")


def json_response(data, status=200):
    return jsonify({"success": True, "data": data}), status


def json_error(message, status=400):
    return jsonify({"success": False, "error": message}), status


def log_request(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        code = result[1] if isinstance(result, tuple) else 200
        log.info(f"{request.method} {request.path} -> {code} ({elapsed*1000:.1f}ms)")
        return result
    return wrapper


def ensure_model(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not predict_service._loaded:
            try:
                predict_service.load()
            except FileNotFoundError:
                return json_error("Model not found. Run train.py first.", 503)
            except Exception as e:
                return json_error(f"Model load failed: {e}", 503)
        return f(*args, **kwargs)
    return wrapper


@app.route("/api/predict", methods=["POST"])
@log_request
@ensure_model
def api_predict():
    if "file" not in request.files:
        return json_error("No file uploaded")
    file = request.files["file"]
    if file.filename == "":
        return json_error("No file selected")
    if not allowed_file(file.filename):
        return json_error("Unsupported file type. Use CSV or Parquet.")
    if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
        return json_error(f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit")
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(config.UPLOAD_DIR, filename)
        file.save(filepath)
        log.info(f"Saved upload: {file.filename} ({os.path.getsize(filepath)} bytes)")
        df = load_file_data(filepath)
        result = predict_service.predict(df)
        os.remove(filepath)
        return json_response(result)
    except ValueError as e:
        return json_error(str(e))
    except RuntimeError as e:
        return json_error(str(e), 503)
    except Exception as e:
        log.exception("Prediction failed")
        return json_error(f"Prediction failed: {e}", 500)


@app.route("/api/predict-batch", methods=["POST"])
@log_request
@ensure_model
def api_predict_batch():
    body = request.get_json(silent=True)
    if not body or "features" not in body:
        return json_error("Send JSON with 'features' array")
    features = body["features"]
    if not isinstance(features, list) or len(features) == 0:
        return json_error("'features' must be a non-empty array")
    df = pd.DataFrame(features)
    result = predict_service.predict(df)
    return json_response(result)


@app.route("/api/status", methods=["GET"])
@log_request
def api_status():
    loaded = getattr(predict_service, '_loaded', False)
    return json_response({
        "status": "online",
        "model_loaded": loaded,
        "timestamp": pd.Timestamp.now().isoformat(),
    })


@app.route("/api/health", methods=["GET"])
@log_request
def api_health():
    loaded = getattr(predict_service, '_loaded', False)
    return json_response({
        "status": "healthy",
        "model": "loaded" if loaded else "not_loaded",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - app._start_time, 1) if hasattr(app, '_start_time') else 0,
    })


@app.route("/api/models", methods=["GET"])
@log_request
def api_models():
    models = []
    if config.MODEL_PATH.exists():
        models.append({
            "name": config.MODEL_PATH.name,
            "path": str(config.MODEL_PATH),
            "size_bytes": os.path.getsize(config.MODEL_PATH),
        })
    if config.BEST_MODEL_PATH.exists() and config.BEST_MODEL_PATH != config.MODEL_PATH:
        models.append({
            "name": config.BEST_MODEL_PATH.name,
            "path": str(config.BEST_MODEL_PATH),
            "size_bytes": os.path.getsize(config.BEST_MODEL_PATH),
        })
    return json_response({
        "available": len(models) > 0,
        "loaded": getattr(predict_service, '_loaded', False),
        "models": models,
    })


@app.route("/api/config", methods=["GET"])
@log_request
def api_config():
    return json_response({
        "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
        "num_classes": len(predict_service.class_names) if predict_service.class_names is not None else 0,
        "input_dim": predict_service.input_dim if predict_service.input_dim else 0,
    })


try:
    predict_service.load()
    log.info(f"Model loaded. Classes: {predict_service.class_names}")
except FileNotFoundError as e:
    log.warning(f"{e}. API running without ML inference. Run train.py to enable.")
except Exception as e:
    log.warning(f"Model load failed: {e}")

app._start_time = time.time()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
