"""Centralized baselines for AIPFL-IDS.

Answers the question a reviewer always asks: *how much does federated
averaging actually cost?*  A baseline is trained on the **same raw-first
stratified split** and the **same train-only preprocessing bundle** as the
federated run, so the numbers are directly comparable to
`training_summary_<dataset>.json`.

Run:
    python baselines.py --dataset NF-ToN-IoT-V2 --model rf
    python baselines.py --dataset CICIoT2023 --model logreg --max-train 50000

Design notes:
  * Top-level imports are sklearn/numpy only — no TensorFlow — so the test
    suite and CI can import this module cheaply.
  * Data loading lives in `main()` and imports `train` lazily (it pulls in
    TensorFlow through `src.model`).
"""

import argparse
import json
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             f1_score, precision_recall_fscore_support)

import config


def build_estimator(model, seed, n_estimators=200, max_iter=1000):
    """Instantiate a baseline. Both models are centralized (single process)."""
    if model == "rf":
        return RandomForestClassifier(
            n_estimators=int(n_estimators),
            random_state=int(seed),
            n_jobs=-1,
        )
    if model == "logreg":
        # lbfgs handles multiclass without materializing a full coefficient
        # matrix per class pair; max_iter guards against slow convergence.
        return LogisticRegression(
            max_iter=int(max_iter),
            solver="lbfgs",
            random_state=int(seed),
        )
    raise ValueError(f"Unknown baseline '{model}'. Use 'rf' or 'logreg'.")


def run_baseline(model, X_train, y_train, X_test, y_test, class_names,
                 seed=None, n_estimators=200, max_iter=1000):
    """Fit a centralized baseline and return honest, measured metrics only.

    Never invents values: ECE/benign-FPR/ROC-AUC are computed when the
    estimator exposes probabilities, otherwise they are None.
    """
    from src.evaluation import benign_false_positive_rate, expected_calibration_error

    seed = config.SEED if seed is None else seed
    class_names = [str(c) for c in class_names]
    est = build_estimator(model, seed, n_estimators=n_estimators, max_iter=max_iter)

    t0 = time.time()
    est.fit(X_train, y_train)
    fit_seconds = time.time() - t0

    t0 = time.time()
    y_pred = est.predict(X_test)
    predict_seconds = time.time() - t0

    probs = None
    if hasattr(est, "predict_proba"):
        try:
            probs = est.predict_proba(X_test)
        except Exception:
            probs = None

    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, labels=list(range(len(class_names))), zero_division=0)
    per_class = {c: {"precision": float(p), "recall": float(r), "f1": float(f)}
                 for c, p, r, f in zip(class_names, prec, rec, f1)}

    metrics = {
        "model": model,
        "test_accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "per_class": per_class,
        "ece": float(expected_calibration_error(y_test, probs)) if probs is not None else None,
        "benign_fpr": benign_false_positive_rate(y_test, y_pred, class_names),
        "fit_seconds": float(fit_seconds),
        "predict_seconds": float(predict_seconds),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "seed": int(seed),
        "params": {"n_estimators": int(n_estimators), "max_iter": int(max_iter)}
        if model == "rf" else {"max_iter": int(max_iter)},
    }
    return metrics, est


def main():
    ap = argparse.ArgumentParser(description="Centralized baseline vs federated run")
    ap.add_argument("--dataset", choices=["CICIoT2023", "NF-ToN-IoT-V2"], default="CICIoT2023")
    ap.add_argument("--model", choices=["rf", "logreg"], default="rf")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--n-estimators", type=int, default=200)
    ap.add_argument("--max-train", type=int, default=None,
                    help="Cap training rows (same uniform subsample for test untouched)")
    args = ap.parse_args()

    # Lazy: `train` pulls in TensorFlow.
    from src.preprocessing import encode_labels, fit_preprocessor, transform_with_bundle
    from src.splits import stratified_splits
    from train import dataset_fingerprint, load_dataset

    seed = args.seed if args.seed is not None else config.SEED
    dataset = args.dataset

    df = load_dataset(dataset)
    label_col = (config.NFTONIOTV2_LABEL_COL if dataset == "NF-ToN-IoT-V2"
                 else config.CICIOT2023_LABEL_COL)

    drop_cols = [label_col]
    if "Label" in df.columns and label_col != "Label":
        drop_cols.append("Label")
    X_raw = df.drop(columns=drop_cols, errors="ignore")
    y_raw = df[label_col].astype(str)
    fingerprint, fp_payload = dataset_fingerprint(df, label_col)

    X_tr_df, X_va_df, X_te_df, y_tr, y_va, y_te = stratified_splits(X_raw, y_raw, seed=seed)
    print(f"Split: train={len(X_tr_df):,}  val={len(X_va_df):,}  test={len(X_te_df):,}")

    y_train, label_encoder = encode_labels(y_tr, fit=True)
    y_test = label_encoder.transform(y_te.astype(str))
    X_train, bundle, scaler = fit_preprocessor(X_tr_df)
    X_test = transform_with_bundle(X_te_df, bundle, scaler)

    if args.max_train and args.max_train < len(X_train):
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(X_train), size=args.max_train, replace=False)
        X_train, y_train = X_train[idx], y_train[idx]
        print(f"Capped training rows to {args.max_train:,}")

    metrics, _ = run_baseline(
        args.model, X_train, y_train, X_test, y_test,
        list(label_encoder.classes_), seed=seed, n_estimators=args.n_estimators)

    metrics["dataset"] = dataset
    metrics["split"] = {
        "train": int(len(X_train)), "val": int(len(X_va_df)), "test": int(len(X_test)),
        "test_split": config.TEST_SPLIT, "val_split": config.VALIDATION_SPLIT,
        "seed": int(seed), "split_mode": "stratified",
        "protocol": "stratified-raw-first; preprocess-fit-train-only; test-once",
    }
    metrics["dataset_fingerprint"] = fingerprint
    metrics["rows_sampled"] = int(fp_payload["rows"])
    metrics["classes"] = list(label_encoder.classes_)

    out = config.RESULTS_DIR / f"baseline_{args.model}_{dataset}.json"
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{args.model.upper()} on {dataset}: "
          f"acc={metrics['test_accuracy']:.4f}  macro-F1={metrics['macro_f1']:.4f}  "
          f"balanced-acc={metrics['balanced_accuracy']:.4f}  "
          + (f"ECE={metrics['ece']:.4f}  " if metrics["ece"] is not None else "")
          + f"({metrics['fit_seconds']:.1f}s fit)")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
