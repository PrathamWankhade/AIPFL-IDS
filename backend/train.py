import os
import sys
import json
import glob
import argparse

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import config
from src.utils import setup_environment
from src.preprocessing import encode_labels, save_preprocessing_artifacts
from src.model import create_model
from src.federated import create_clients, federated_training_loop
from src.evaluation import evaluate_model


def load_dataset(dataset):
    if dataset == "NF-ToN-IoT-V2":
        return load_nftoniotv2()
    return load_ciciot2023()


# Raw per-class totals from the last load_* call (pass-1 census), recorded
# in the training summary so balanced-sample metrics can be distinguished
# from natural-prevalence performance. Not a substitute for a
# prevalence-representative test set (see docs).
LAST_RAW_TOTALS: dict = {}


def dataset_fingerprint(df, label_col):
    """Deterministic fingerprint of the SAMPLED frame (not a raw-data hash)."""
    import hashlib
    import json as _json
    vc = df[label_col].astype(str).value_counts().sort_index()
    payload = {"rows": int(len(df)), "columns": sorted(map(str, df.columns)),
               "class_counts": {str(k): int(v) for k, v in vc.items()}}
    return hashlib.sha256(_json.dumps(payload, sort_keys=True).encode()).hexdigest(), payload


def load_nftoniotv2():
    dataset_path = config.DATA_DIR / "raw" / config.NFTONIOTV2_FILE
    if not os.path.exists(dataset_path):
        print("Downloading NF-ToN-IoT-V2 from KaggleHub...")
        try:
            import kagglehub
            path = kagglehub.dataset_download(config.NFTONIOTV2_SOURCE)
            df = pd.read_parquet(os.path.join(path, config.NFTONIOTV2_FILE))
            df.to_parquet(dataset_path, index=False)
            print(f"Cached to {dataset_path}")
        except Exception as e:
            print(f"Download failed: {e}")
            sys.exit(1)
    else:
        print(f"Loading cached dataset: {dataset_path}")
    import pyarrow.parquet as pq
    rng = np.random.default_rng(config.RANDOM_STATE)
    # Pass 1: per-class totals (label column only) for unbiased fractions.
    pf = pq.ParquetFile(dataset_path)
    totals = {}
    for batch in pf.iter_batches(batch_size=200000, columns=[config.NFTONIOTV2_LABEL_COL]):
        chunk = batch.to_pandas(types_mapper=None)
        vc = chunk[config.NFTONIOTV2_LABEL_COL].value_counts()
        for k, v in vc.items():
            totals[k] = totals.get(k, 0) + int(v)
    print(f"Class totals (raw): {len(totals)} classes")
    LAST_RAW_TOTALS.clear()
    LAST_RAW_TOTALS.update({str(k): int(v) for k, v in totals.items()})
    fractions = {k: min(1.0, config.NFTONIOTV2_MAX_SAMPLES_PER_CLASS / max(1, v)) for k, v in totals.items()}
    # Pass 2: stratified sample with fixed seed (avoids first-rows bias).
    pf = pq.ParquetFile(dataset_path)
    collected = {}
    seed_seq = 0
    for batch in pf.iter_batches(batch_size=200000):
        chunk = batch.to_pandas(types_mapper=None)
        for attack in chunk[config.NFTONIOTV2_LABEL_COL].unique():
            mask = chunk[config.NFTONIOTV2_LABEL_COL] == attack
            attack_rows = chunk[mask]
            frac = fractions.get(attack, 1.0)
            if frac < 1.0 and len(attack_rows):
                attack_rows = attack_rows.sample(frac=frac, random_state=int(config.RANDOM_STATE + seed_seq) % (2**31 - 1))
            if attack not in collected:
                collected[attack] = attack_rows
            else:
                collected[attack] = pd.concat([collected[attack], attack_rows], ignore_index=True)
        seed_seq += 1
    # Deterministic cap to MAX_SAMPLES_PER_CLASS (uniform subsample, not first-rows).
    final_parts = []
    for attack, part in collected.items():
        if len(part) > config.NFTONIOTV2_MAX_SAMPLES_PER_CLASS:
            part = part.sample(n=config.NFTONIOTV2_MAX_SAMPLES_PER_CLASS, random_state=config.RANDOM_STATE)
        final_parts.append(part)
    df = pd.concat(final_parts, ignore_index=True)
    df = df.sample(frac=1, random_state=config.RANDOM_STATE).reset_index(drop=True)
    print(f"Dataset shape: {df.shape}")
    return df


CICIOT_CLASS_MAP = {
    "DDOS-ACK_FRAGMENTATION": "DDOS", "DDOS-HTTP_FLOOD": "DDOS", "DDOS-ICMP_FLOOD": "DDOS",
    "DDOS-ICMP_FRAGMENTATION": "DDOS", "DDOS-PSHACK_FLOOD": "DDOS", "DDOS-RSTFINFLOOD": "DDOS",
    "DDOS-SLOWLORIS": "DDOS", "DDOS-SYNONYMOUSIP_FLOOD": "DDOS", "DDOS-SYN_FLOOD": "DDOS",
    "DDOS-TCP_FLOOD": "DDOS", "DDOS-UDP_FLOOD": "DDOS", "DDOS-UDP_FRAGMENTATION": "DDOS",
    "DOS-HTTP_FLOOD": "DOS", "DOS-SYN_FLOOD": "DOS", "DOS-TCP_FLOOD": "DOS", "DOS-UDP_FLOOD": "DOS",
    "MIRAI-GREETH_FLOOD": "MIRAI", "MIRAI-GREIP_FLOOD": "MIRAI", "MIRAI-UDPPLAIN": "MIRAI",
    "RECON-HOSTDISCOVERY": "RECON", "RECON-OSSCAN": "RECON", "RECON-PINGSWEEP": "RECON", "RECON-PORTSCAN": "RECON",
    "BACKDOOR_MALWARE": "OTHER", "BROWSERHIJACKING": "OTHER", "COMMANDINJECTION": "OTHER",
    "SQLINJECTION": "OTHER", "UPLOADING_ATTACK": "OTHER", "XSS": "OTHER",
}


def merge_ciciot_classes(label):
    return CICIOT_CLASS_MAP.get(label, label)


def load_ciciot2023():
    pattern = os.path.join(config.DATA_DIR, config.CICIOT2023_PATTERN)
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(
            f"No CICIoT2023 CSVs matched {pattern!r}. The raw dataset is not "
            "bundled with this repository: fetch 'dhoogla/ciciot2023' (Kaggle) or "
            "the original UNB release, then lay the CSVs out under "
            "backend/data/raw/CICIoT2023 */. NF-ToN-IoT-V2 does not need this "
            "step — it downloads itself on first run."
        )
    print(f"Loading CICIoT2023 from {len(files)} CSV files...")
    # Pass 1: count per merged class (label column only) for unbiased fractions.
    totals = {}
    total_rows = 0
    for fpath in files:
        chunk = pd.read_csv(fpath, usecols=[config.CICIOT2023_LABEL_COL])
        chunk[config.CICIOT2023_LABEL_COL] = chunk[config.CICIOT2023_LABEL_COL].astype(str).str.strip()
        chunk = chunk[~chunk[config.CICIOT2023_LABEL_COL].isin(["nan", "", "NaN", "None"])]
        chunk[config.CICIOT2023_LABEL_COL] = chunk[config.CICIOT2023_LABEL_COL].map(merge_ciciot_classes)
        total_rows += len(chunk)
        vc = chunk[config.CICIOT2023_LABEL_COL].value_counts()
        for k, v in vc.items():
            totals[k] = totals.get(k, 0) + int(v)
    fractions = {k: min(1.0, config.CICIOT2023_MAX_SAMPLES_PER_CLASS / max(1, v)) for k, v in totals.items()}
    # Pass 2: stratified sample per file with fixed seeds.
    collected = {}
    for idx, fpath in enumerate(files):
        chunk = pd.read_csv(fpath)
        chunk[config.CICIOT2023_LABEL_COL] = chunk[config.CICIOT2023_LABEL_COL].astype(str).str.strip()
        chunk = chunk[~chunk[config.CICIOT2023_LABEL_COL].isin(["nan", "", "NaN", "None"])]
        chunk[config.CICIOT2023_LABEL_COL] = chunk[config.CICIOT2023_LABEL_COL].map(merge_ciciot_classes)
        for attack in chunk[config.CICIOT2023_LABEL_COL].unique():
            mask = chunk[config.CICIOT2023_LABEL_COL] == attack
            attack_rows = chunk[mask]
            frac = fractions.get(attack, 1.0)
            if frac < 1.0 and len(attack_rows):
                attack_rows = attack_rows.sample(frac=frac, random_state=int(config.RANDOM_STATE + idx) % (2**31 - 1))
            if attack not in collected:
                collected[attack] = attack_rows
            else:
                collected[attack] = pd.concat([collected[attack], attack_rows], ignore_index=True)
        if idx % 10 == 0 or idx == len(files) - 1:
            done = sum(len(v) for v in collected.values())
            print(f"  [{idx+1}/{len(files)}] {done:>8,} sampled rows")
    final_parts = []
    for attack, part in collected.items():
        if len(part) > config.CICIOT2023_MAX_SAMPLES_PER_CLASS:
            part = part.sample(n=config.CICIOT2023_MAX_SAMPLES_PER_CLASS, random_state=config.RANDOM_STATE)
        final_parts.append(part)
    df = pd.concat(final_parts, ignore_index=True)
    df = df.sample(frac=1, random_state=config.RANDOM_STATE).reset_index(drop=True)
    print(f"\nTotal raw rows : {total_rows:,}")
    LAST_RAW_TOTALS.clear()
    LAST_RAW_TOTALS.update({str(k): int(v) for k, v in totals.items()})
    print(f"Balanced shape : {df.shape}")
    print(f"Classes        : {len(collected)}")
    for attack in sorted(collected.keys(), key=str):
        print(f"  {attack:<35} {len(collected[attack]):>6,}")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["CICIoT2023", "NF-ToN-IoT-V2"], default="CICIoT2023")
    ap.add_argument("--seed", type=int, default=None, help="Override AIPFL_SEED for reproducibility runs")
    ap.add_argument("--partition", choices=["iid", "label_skew", "quantity_skew"], default=None)
    ap.add_argument("--alpha", type=float, default=None, help="Dirichlet alpha for non-IID partitions")
    ap.add_argument("--client-fraction", type=float, default=None, help="Fraction of clients sampled per round")
    ap.add_argument("--split", choices=["stratified", "group"], default="stratified",
                    help="stratified: random rows; group: hold out whole groups (capture/device/time)")
    ap.add_argument("--group-col", default=None,
                    help="Column holding capture/device/session id for --split group")
    args = ap.parse_args()
    dataset = args.dataset
    if args.seed is not None:
        config.SEED = args.seed
        config.RANDOM_STATE = args.seed
    partition = args.partition or config.CLIENT_PARTITION
    alpha = args.alpha if args.alpha is not None else config.DIRICHLET_ALPHA
    client_fraction = args.client_fraction if args.client_fraction is not None else config.CLIENT_FRACTION

    setup_environment()
    print(f"\n{'#'*60}\nTraining on {dataset}\n{'#'*60}")

    df = load_dataset(dataset)

    if dataset == "NF-ToN-IoT-V2":
        label_col = config.NFTONIOTV2_LABEL_COL
        scaler_path = config.NFTONIOTV2_SCALER
        encoder_path = config.NFTONIOTV2_ENCODER
        feature_path = config.NFTONIOTV2_FEATURES
        model_path = config.NFTONIOTV2_MODEL_PATH
        best_path = config.NFTONIOTV2_BEST_PATH
    else:
        label_col = config.CICIOT2023_LABEL_COL
        scaler_path = config.CICIOT2023_SCALER
        encoder_path = config.CICIOT2023_ENCODER
        feature_path = config.CICIOT2023_FEATURES
        model_path = config.CICIOT2023_MODEL_PATH
        best_path = config.CICIOT2023_BEST_PATH

    print(f"\n{'='*60}\nDataset Exploration\n{'='*60}")
    print(f"Shape       : {df.shape}")
    print(f"Columns     : {list(df.columns)[:10]}... ({len(df.columns)} total)")
    print(f"Memory      : {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    fingerprint, fp_payload = dataset_fingerprint(df, label_col)
    print(f"Sample fingerprint: {fingerprint[:16]}… ({fp_payload['rows']:,} rows)")

    drop_cols = [label_col]
    if "Label" in df.columns and label_col != "Label":
        drop_cols.append("Label")
    if args.group_col and args.group_col in df.columns:
        # Identifiers must never become model features.
        drop_cols.append(args.group_col)
    X_raw = df.drop(columns=drop_cols, errors="ignore")
    y_raw = df[label_col].astype(str)

    # ── Split FIRST on raw records (no preprocessing fitted yet) ──
    split_protocol = "stratified-raw-first; preprocess-fit-train-only; val-selects-checkpoint; test-once"
    if args.split == "group":
        from sklearn.model_selection import GroupShuffleSplit
        if not args.group_col or args.group_col not in df.columns:
            raise ValueError("--split group requires --group-col naming a capture/device/session column present in the data.")
        groups = df[args.group_col].astype(str).to_numpy()
        gss_test = GroupShuffleSplit(n_splits=1, test_size=config.TEST_SPLIT, random_state=config.SEED)
        tr_val_idx, te_idx = next(gss_test.split(X_raw, y_raw, groups))
        val_frac = config.VALIDATION_SPLIT / (1.0 - config.TEST_SPLIT)
        gss_val = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=config.SEED)
        tr_idx_rel, va_idx_rel = next(gss_val.split(
            X_raw.iloc[tr_val_idx], y_raw.iloc[tr_val_idx], groups[tr_val_idx]))
        tr_idx = tr_val_idx[tr_idx_rel]
        va_idx = tr_val_idx[va_idx_rel]
        X_tr_df, X_va_df, X_te_df = X_raw.iloc[tr_idx], X_raw.iloc[va_idx], X_raw.iloc[te_idx]
        y_tr, y_va, y_te = y_raw.iloc[tr_idx], y_raw.iloc[va_idx], y_raw.iloc[te_idx]
        split_protocol = (f"group-holdout on {args.group_col}; no group spans splits; "
                          "preprocess-fit-train-only; val-selects-checkpoint; test-once")
    else:
        try:
            X_tr_df, X_te_df, y_tr, y_te = train_test_split(
                X_raw, y_raw, test_size=config.TEST_SPLIT,
                stratify=y_raw, random_state=config.SEED)
            val_frac = config.VALIDATION_SPLIT / (1.0 - config.TEST_SPLIT)
            X_tr_df, X_va_df, y_tr, y_va = train_test_split(
                X_tr_df, y_tr, test_size=val_frac,
                stratify=y_tr, random_state=config.SEED)
        except ValueError:
            # Fallback for degenerate tiny/rare-class samples.
            X_tr_df, X_te_df, y_tr, y_te = train_test_split(
                X_raw, y_raw, test_size=config.TEST_SPLIT, random_state=config.SEED)
            val_frac = config.VALIDATION_SPLIT / (1.0 - config.TEST_SPLIT)
            X_tr_df, X_va_df, y_tr, y_va = train_test_split(
                X_tr_df, y_tr, test_size=val_frac, random_state=config.SEED)
    print(f"Split (raw-first): train={len(X_tr_df):,}  val={len(X_va_df):,}  test={len(X_te_df):,}")

    # ── Fit encoder + preprocessor on TRAIN only ──
    from src.preprocessing import fit_preprocessor, transform_with_bundle
    y_train, label_encoder = encode_labels(y_tr, fit=True)
    class_names = label_encoder.classes_
    num_classes = len(class_names)
    print(f"\nClasses: {num_classes} {list(class_names)}")
    try:
        y_val = label_encoder.transform(y_va.astype(str))
        y_test = label_encoder.transform(y_te.astype(str))
    except ValueError as e:
        raise ValueError(f"Validation/test contains label unseen in train split: {e}")

    X_train, bundle, scaler = fit_preprocessor(X_tr_df)
    feature_columns = bundle["feature_columns"]
    X_val = transform_with_bundle(X_va_df, bundle, scaler)
    X_test = transform_with_bundle(X_te_df, bundle, scaler)
    input_dim = X_train.shape[1]
    print(f"Input features: {input_dim}")

    clients, client_sizes = create_clients(X_train, y_train, partition=partition, alpha=alpha, seed=config.SEED)
    from src.federated import client_label_histogram
    hist = client_label_histogram([y for _, y in clients], num_classes=num_classes)
    print(f"Federated clients: {len(clients)} partition={partition} alpha={alpha}")
    print(f"Client sizes: {client_sizes}")
    print(f"Client label histograms saved to training summary.")

    global_model = create_model(input_dim, num_classes)
    global_model.summary()

    print(f"\nTraining: {config.GLOBAL_ROUNDS} rounds, {config.EPOCHS_PER_CLIENT} epochs/client, {config.NUM_CLIENTS} clients, lr={config.LEARNING_RATE}")
    result = federated_training_loop(global_model, clients, client_sizes, X_val, y_val, input_dim, num_classes, verbose=True, best_model_path=best_path, final_model_path=model_path, client_fraction=client_fraction, seed=config.SEED)

    # ── P0 fix: metrics must describe the DEPLOYED checkpoint ──
    # 1. Persist preprocessing first so reload uses matching artifacts.
    # 2. Promote best-val checkpoint to the serving path.
    # 3. Reload that exact file from disk and evaluate ONCE on test.
    import shutil
    save_preprocessing_artifacts(scaler, label_encoder, scaler_path, encoder_path, feature_path, feature_columns, bundle=bundle)
    if result["best_accuracy"] > 0 and os.path.exists(best_path):
        shutil.copyfile(best_path, model_path)
        print(f"Promoted best-val checkpoint -> {model_path}")
    else:
        result["model"].save(model_path)
        print(f"No best checkpoint; saved final-round model -> {model_path}")

    import tensorflow as tf
    from src.preprocessing import load_preprocessing_artifacts
    deployed_model = tf.keras.models.load_model(str(model_path))
    _scaler, _encoder, _cols, _bundle = load_preprocessing_artifacts(dataset)
    assert list(_cols) == list(feature_columns), "Feature schema changed between save and reload."
    assert list(_encoder.classes_) == list(label_encoder.classes_), "Label map changed between save and reload."
    assert deployed_model.input_shape[1] == input_dim, "Reloaded model input dim mismatch."
    # Final held-out evaluation runs ONCE on test (never used for selection),
    # on the exact artifact that will be served.
    eval_results = evaluate_model(deployed_model, X_test, y_test, class_names, history=result["history"])
    print(f"\nModel: {model_path}")
    print(f"Scaler: {scaler_path}")
    print(f"Encoder: {encoder_path}")

    summary_path = config.RESULTS_DIR / f"training_summary_{dataset}.json"
    val_acc = result["history"]["val_accuracy"][-1] if result["history"]["val_accuracy"] else result["best_accuracy"]
    summary = {
        "dataset": dataset,
        "best_val_accuracy": result["best_accuracy"],
        "final_val_accuracy": val_acc,
        "test_accuracy": eval_results["test_accuracy"],
        "test_loss": eval_results["test_loss"],
        "macro_f1": eval_results.get("macro_f1"),
        "balanced_accuracy": eval_results.get("balanced_accuracy"),
        "roc_auc_macro_ovr": eval_results.get("roc_auc_macro_ovr"),
        "ece": eval_results.get("ece"),
        "benign_fpr": eval_results.get("benign_fpr"),
        "per_class": eval_results.get("per_class"),
        "participating_clients": result["history"].get("participating_clients", []),
        "comm_bytes_upload": result["history"].get("comm_bytes_upload", []),
        "partition": partition,
        "dirichlet_alpha": alpha,
        "client_fraction": client_fraction,
        "client_sizes": [int(s) for s in client_sizes],
        "client_label_histograms": [{str(k): int(v) for k, v in h.items()} for h in hist],
        "input_dim": int(input_dim),
        "num_classes": int(num_classes),
        "class_names": [str(c) for c in class_names],
        "feature_columns": list(feature_columns),
        "split": {"train": len(X_train), "val": len(X_val), "test": len(X_test),
                  "test_split": config.TEST_SPLIT, "val_split": config.VALIDATION_SPLIT,
                  "seed": config.SEED, "split_mode": args.split,
                  "group_col": args.group_col, "protocol": split_protocol},
        "sampling": {"method": "two-pass stratified fraction + deterministic cap",
                     "per_class_cap": config.CICIOT2023_MAX_SAMPLES_PER_CLASS
                     if dataset == "CICIoT2023" else config.NFTONIOTV2_MAX_SAMPLES_PER_CLASS,
                     "seed": config.RANDOM_STATE,
                     "raw_class_totals": dict(LAST_RAW_TOTALS),
                     "sampled_class_counts": fp_payload["class_counts"],
                     "dataset_fingerprint": fingerprint,
                     "note": "Balanced-sample metrics; retain a natural-prevalence test set for operational FPR/precision."},
        "config": {
            "global_rounds": config.GLOBAL_ROUNDS,
            "local_epochs": config.EPOCHS_PER_CLIENT,
            "num_clients": config.NUM_CLIENTS,
            "batch_size": config.BATCH_SIZE,
            "learning_rate": config.LEARNING_RATE,
            "architecture": config.DENSE_UNITS,
        },
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Release manifest binds model + preprocessing + metrics with hashes.
    def _sha256(p):
        import hashlib
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    release = {
        "release_id": f"{dataset}-{pd.Timestamp.now().strftime('%Y%m%d')}",
        "dataset": dataset,
        "model_file": os.path.basename(model_path),
        "best_val_accuracy": result["best_accuracy"],
        "test_accuracy": eval_results["test_accuracy"],
        "feature_columns": list(feature_columns),
        "class_names": [str(c) for c in class_names],
        "training_summary": os.path.basename(summary_path),
        "artifact_sha256": {},
    }
    for p in [model_path, scaler_path, encoder_path, feature_path]:
        try:
            release["artifact_sha256"][os.path.basename(p)] = _sha256(p)
        except Exception:
            pass
    with open(config.RESULTS_DIR / f"release_{dataset}.json", "w") as f:
        json.dump(release, f, indent=2)

    print(f"\n{'#'*60}\n{dataset} Training Complete!\nBest Val Accuracy: {result['best_accuracy']:.4f}\nTest Accuracy: {eval_results['test_accuracy']:.4f}\n{'#'*60}")


if __name__ == "__main__":
    main()
