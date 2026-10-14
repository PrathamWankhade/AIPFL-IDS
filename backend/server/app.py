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

from src.predict import get_service
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE_MB * 1024 * 1024
CORS(app, origins=config.ALLOWED_ORIGINS, supports_credentials=False)

ALLOWED_EXTENSIONS = {".csv", ".parquet"}


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def load_file_data(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        # nrows guard happens after load via shape check; chunks would need
        # a job queue (Phase 3). Refuse decompression bombs via size cap first.
        return pd.read_csv(filepath)
    elif ext == ".parquet":
        return pd.read_parquet(filepath)
    raise ValueError(f"Unsupported file type: {ext}")


def check_frame_bounds(df):
    if df.shape[0] == 0:
        raise ValueError("Uploaded file contains no data rows.")
    if df.shape[0] > config.MAX_UPLOAD_ROWS:
        raise ValueError(f"File has {df.shape[0]:,} rows; limit is {config.MAX_UPLOAD_ROWS:,}. Split the file or use a job queue.")
    if df.shape[1] > config.MAX_UPLOAD_COLUMNS:
        raise ValueError(f"File has {df.shape[1]} columns; limit is {config.MAX_UPLOAD_COLUMNS}.")


@app.errorhandler(413)
def _too_large(_e):
    return json_error(f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit", 413)


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


def resolve_service(dataset=None):
    ds = dataset or request.args.get("dataset", "CICIoT2023")
    if ds not in ("CICIoT2023", "NF-ToN-IoT-V2"):
        return None, json_error(f"Invalid dataset '{ds}'. Use 'CICIoT2023' or 'NF-ToN-IoT-V2'.", 400)
    svc = get_service(ds)
    if not svc._loaded:
        try:
            svc.load()
        except FileNotFoundError as e:
            return None, json_error(str(e), 503)
        except Exception as e:
            return None, json_error(f"Model load failed: {e}", 503)
    return svc, None


@app.route("/api/jobs", methods=["POST"])
@log_request
def api_jobs_create():
    """Enqueue a large-file inference job. Returns 202 + job_id; poll status."""
    import tempfile
    from src import jobs as jobstore
    dataset = request.args.get("dataset", "CICIoT2023")
    svc, err = resolve_service(dataset)
    if err:
        return err
    if "file" not in request.files:
        return json_error("No file uploaded")
    file = request.files["file"]
    if file.filename == "":
        return json_error("No file selected")
    if not allowed_file(file.filename):
        return json_error("Unsupported file type. Use CSV or Parquet.")
    if request.content_length and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
        return json_error(f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit", 413)
    ext = os.path.splitext(file.filename)[1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=str(config.UPLOAD_DIR))
    filepath = tmp.name
    tmp.close()
    file.save(filepath)
    try:
        # Bound the shape before accepting the job (same caps as sync).
        df_probe = load_file_data(filepath)
        check_frame_bounds(df_probe)
        del df_probe
    except ValueError as e:
        try:
            os.remove(filepath)
        except Exception:
            pass
        return json_error(str(e), 422)

    job_id = jobstore.create_job(dataset, ext)
    jdir = jobstore.jobs_dir(config.UPLOAD_DIR)

    def _work():
        try:
            df = load_file_data(filepath)
            check_frame_bounds(df)
            result = svc.predict(df)
            csv_path = str(jdir / f"{job_id}.csv")
            import csv as _csv
            with open(csv_path, "w", newline="") as f:
                w = _csv.writer(f)
                w.writerow(["prediction", "confidence"])
                for r in result["results"]:
                    w.writerow([r["prediction"], r["confidence"]])
            with jobstore._LOCK:
                if job_id in jobstore._JOBS:
                    jobstore._JOBS[job_id]["result_csv"] = csv_path
            return {"total": result["total"], "distribution": result["distribution"],
                    "mean_confidence": result["mean_confidence"]}
        finally:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass

    jobstore.run_in_background(_work, job_id)
    return jsonify({"success": True, "data": {"job_id": job_id, "status": "queued"}}), 202


@app.route("/api/jobs/<job_id>", methods=["GET"])
@log_request
def api_jobs_status(job_id):
    from src import jobs as jobstore
    job = jobstore.public_view(jobstore.get_job(job_id))
    if not job:
        return json_error("Unknown job_id", 404)
    return json_response(job)


@app.route("/api/jobs/<job_id>/download", methods=["GET"])
@log_request
def api_jobs_download(job_id):
    from flask import send_file
    from src import jobs as jobstore
    job = jobstore.get_job(job_id)
    if not job:
        return json_error("Unknown job_id", 404)
    if job.get("status") != "done" or not job.get("result_csv"):
        return json_error(f"Job {job.get('status')}; download not ready", 409)
    return send_file(job["result_csv"], mimetype="text/csv", as_attachment=True,
                     download_name=f"predictions_{job_id}.csv")


@app.route("/api/predict", methods=["POST"])
@log_request
def api_predict():
    import tempfile
    dataset = request.args.get("dataset", "CICIoT2023")
    svc, err = resolve_service(dataset)
    if err:
        return err
    if "file" not in request.files:
        return json_error("No file uploaded")
    file = request.files["file"]
    if file.filename == "":
        return json_error("No file selected")
    if not allowed_file(file.filename):
        return json_error("Unsupported file type. Use CSV or Parquet.")
    # Flask enforces app.config["MAX_CONTENT_LENGTH"] -> 413; this is a
    # defense-in-depth check for chunked uploads without Content-Length.
    if request.content_length and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
        return json_error(f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit", 413)
    ext = os.path.splitext(file.filename)[1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=str(config.UPLOAD_DIR))
    filepath = tmp.name
    tmp.close()
    request_id = uuid.uuid4().hex[:12]
    try:
        file.save(filepath)
        log.info(f"[{request_id}] upload received ({os.path.getsize(filepath)} bytes, {ext})")
        df = load_file_data(filepath)
        check_frame_bounds(df)
        result = svc.predict(df)
        result["dataset"] = dataset
        result["request_id"] = request_id
        return json_response(result)
    except ValueError as e:
        return json_error(str(e), 422)
    except RuntimeError as e:
        return json_error(str(e), 503)
    except Exception as e:
        log.exception(f"[{request_id}] Prediction failed")
        return json_error(f"Prediction failed: {e}", 500)
    finally:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass


@app.route("/api/predict-batch", methods=["POST"])
@log_request
def api_predict_batch():
    dataset = request.args.get("dataset", "CICIoT2023")
    svc, err = resolve_service(dataset)
    if err:
        return err
    body = request.get_json(silent=True)
    if not body or "features" not in body:
        return json_error("Send JSON with 'features' array")
    features = body["features"]
    if not isinstance(features, list) or len(features) == 0:
        return json_error("'features' must be a non-empty array")
    if len(features) > config.MAX_BATCH_ROWS:
        return json_error(f"'features' has {len(features)} rows; limit is {config.MAX_BATCH_ROWS}.", 413)
    try:
        df = pd.DataFrame(features)
    except Exception as e:
        return json_error(f"Invalid 'features' payload: {e}", 422)
    if df.shape[1] > config.MAX_UPLOAD_COLUMNS:
        return json_error(f"Payload has {df.shape[1]} columns; limit is {config.MAX_UPLOAD_COLUMNS}.", 413)
    try:
        result = svc.predict(df)
    except ValueError as e:
        return json_error(str(e), 422)
    except RuntimeError as e:
        return json_error(str(e), 503)
    result["dataset"] = dataset
    return json_response(result)


@app.route("/api/status", methods=["GET"])
@log_request
def api_status():
    datasets = {}
    for ds in ("CICIoT2023", "NF-ToN-IoT-V2"):
        svc = get_service(ds)
        datasets[ds] = {
            "model_loaded": svc._loaded,
            "num_classes": len(svc.class_names) if svc.class_names is not None else 0,
            "input_dim": svc.input_dim if svc.input_dim else 0,
        }
    return json_response({
        "status": "online",
        "datasets": datasets,
        "timestamp": pd.Timestamp.now().isoformat(),
    })


@app.route("/api/health", methods=["GET"])
@log_request
def api_health():
    loaded_models = sum(1 for ds in ("CICIoT2023", "NF-ToN-IoT-V2") if get_service(ds)._loaded)
    return json_response({
        "status": "healthy",
        "models_loaded": loaded_models,
        "total_models": 2,
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - app._start_time, 1) if hasattr(app, '_start_time') else 0,
    })


@app.route("/api/livez", methods=["GET"])
def api_livez():
    # Process liveness only; never depends on model files.
    return json_response({"status": "alive"})


@app.route("/api/readyz", methods=["GET"])
def api_readyz():
    # Readiness: model + scaler + schema + dry-run inference per dataset.
    import numpy as np
    details = {}
    ready = True
    for ds in ("CICIoT2023", "NF-ToN-IoT-V2"):
        try:
            svc = get_service(ds)
            if not svc._loaded:
                svc.load()
            if svc.feature_columns is None or svc.scaler is None or svc.label_encoder is None:
                raise RuntimeError("preprocessing artifacts missing")
            n = min(len(svc.feature_columns), 8)
            # fill remaining with zeros to match schema width
            import pandas as _pd  # local alias to avoid shadowing
            _df = _pd.DataFrame([{c: 0.0 for c in svc.feature_columns}])
            svc.predict(_df.head(1))
            details[ds] = {"ready": True, "input_dim": svc.input_dim,
                           "num_classes": len(svc.class_names)}
        except FileNotFoundError as e:
            ready = False
            details[ds] = {"ready": False, "error": str(e)[:200]}
        except Exception as e:
            ready = False
            details[ds] = {"ready": False, "error": f"{type(e).__name__}: {e}"[:200]}
    code = 200 if ready else 503
    return jsonify({"success": ready, "data": {"ready": ready, "datasets": details}}), code


@app.route("/api/models", methods=["GET"])
@log_request
def api_models():
    models = []
    entries = [
        ("CICIoT2023", config.CICIOT2023_MODEL_PATH, config.CICIOT2023_BEST_PATH),
        ("NF-ToN-IoT-V2", config.NFTONIOTV2_MODEL_PATH, config.NFTONIOTV2_BEST_PATH),
    ]
    for name, model_path, best_path in entries:
        if model_path.exists():
            models.append({
                "name": model_path.name,
                "dataset": name,
                "size_bytes": os.path.getsize(model_path),
            })
        if best_path.exists() and best_path != model_path:
            models.append({
                "name": best_path.name,
                "dataset": name,
                "size_bytes": os.path.getsize(best_path),
            })
    return json_response({
        "available": len(models) > 0,
        "models": models,
    })


@app.route("/api/metrics", methods=["GET"])
@log_request
def api_metrics():
    """Actual persisted run statistics only; missing values are null, never invented."""
    import json as _json
    out = {}
    for ds in ("CICIoT2023", "NF-ToN-IoT-V2"):
        summary_path = config.RESULTS_DIR / f"training_summary_{ds}.json"
        release_path = config.RESULTS_DIR / f"release_{ds}.json"
        entry = {"training_summary": None, "release": None}
        for key, path in (("training_summary", summary_path), ("release", release_path)):
            try:
                if path.exists():
                    with open(path) as f:
                        entry[key] = _json.load(f)
            except Exception as e:
                entry[key] = {"error": f"unreadable: {e}"}
        out[ds] = entry
    return json_response({"metrics": out, "note": "Null means not measured. Benchmarks in README are not live telemetry."})


@app.route("/api/config", methods=["GET"])
@log_request
def api_config():
    datasets_info = {}
    for ds in ("CICIoT2023", "NF-ToN-IoT-V2"):
        svc = get_service(ds)
        datasets_info[ds] = {
            "num_classes": len(svc.class_names) if svc.class_names is not None else 0,
            "input_dim": svc.input_dim if svc.input_dim else 0,
            "model_loaded": svc._loaded,
            "class_names": list(svc.class_names) if svc.class_names is not None else [],
        }
    return json_response({
        "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "datasets": datasets_info,
    })


for ds in ("CICIoT2023", "NF-ToN-IoT-V2"):
    svc = get_service(ds)
    try:
        svc.load()
        log.info(f"[{ds}] Model loaded. Classes: {svc.class_names}")
    except FileNotFoundError as e:
        log.warning(f"[{ds}] {e}. Run train.py first.")
    except Exception as e:
        log.warning(f"[{ds}] Model load failed: {e}")

app._start_time = time.time()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
