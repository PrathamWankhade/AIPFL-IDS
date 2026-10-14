"""Streaming job inference: bounded memory regardless of row count.

Sync /api/predict loads the whole frame (capped by MAX_UPLOAD_ROWS). Jobs
stream CSV chunks / Parquet row-groups, predict per chunk, append rows to
the result CSV incrementally, and aggregate only summary statistics —
so /api/jobs genuinely supports files larger than the sync limit, up to
MAX_JOB_ROWS. Memory stays ~one chunk, not the whole file.
"""
import csv as _csv

import config


def _merge_into(acc, result):
    total = result["total"]
    acc["total"] += total
    acc["conf_sum"] += result["mean_confidence"] * total
    for k, v in result["distribution"].items():
        acc["distribution"][k] = acc["distribution"].get(k, 0) + int(v)


def _finish(acc):
    total = acc["total"]
    return {"total": total,
            "distribution": dict(acc["distribution"]),
            "mean_confidence": (acc["conf_sum"] / total) if total else 0.0}


def run_job_file(svc, filepath, ext, csv_out_path, max_rows, chunk_rows=20000):
    """Stream filepath, predict per chunk, write CSV incrementally."""
    import pandas as pd
    acc = {"total": 0, "conf_sum": 0.0, "distribution": {}}
    rows_seen = 0
    first = True

    def _handle(df):
        nonlocal rows_seen, first
        result = svc.predict(df)
        mode = "w" if first else "a"
        with open(csv_out_path, mode, newline="") as f:
            w = _csv.writer(f)
            if first:
                w.writerow(["prediction", "confidence"])
                first = False
            for r in result["results"]:
                w.writerow([r["prediction"], r["confidence"]])
        _merge_into(acc, result)

    if ext == ".csv":
        cols = pd.read_csv(filepath, nrows=0).columns
        if len(cols) > config.MAX_UPLOAD_COLUMNS:
            raise ValueError(
                f"File has {len(cols)} columns; limit is {config.MAX_UPLOAD_COLUMNS}.")
        for chunk in pd.read_csv(filepath, chunksize=chunk_rows):
            rows_seen += len(chunk)
            if rows_seen > max_rows:
                raise ValueError(
                    f"Job file exceeds {max_rows:,} rows.")
            if len(chunk) == 0:
                continue
            _handle(chunk)
    elif ext == ".parquet":
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(filepath)
        if pf.metadata.num_columns > config.MAX_UPLOAD_COLUMNS:
            raise ValueError(
                f"File has {pf.metadata.num_columns} columns; limit is {config.MAX_UPLOAD_COLUMNS}.")
        for batch in pf.iter_batches(batch_size=chunk_rows):
            chunk = batch.to_pandas()
            rows_seen += len(chunk)
            if rows_seen > max_rows:
                raise ValueError(
                    f"Job file exceeds {max_rows:,} rows.")
            if len(chunk) == 0:
                continue
            _handle(chunk)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    if rows_seen == 0:
        raise ValueError("Uploaded file contains no data rows.")
    return _finish(acc)
