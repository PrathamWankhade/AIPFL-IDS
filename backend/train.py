#!/usr/bin/env python
"""AIPFL-IDS training pipeline: load, balance, preprocess, federated train, evaluate."""

import os
import sys
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import config
from src.utils import setup_environment
from src.preprocessing import preprocess_features, encode_labels, save_preprocessing_artifacts
from src.model import create_model
from src.federated import create_clients, federated_training_loop
from src.evaluation import evaluate_model


def load_dataset():
    dataset_path = os.path.join(config.DATA_DIR / "raw", config.DATASET_FILE)
    if os.path.exists(dataset_path):
        print(f"Loading cached dataset: {dataset_path}")
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(dataset_path)
        samples_per_class = {}
        for batch in pf.iter_batches(batch_size=200000):
            chunk = batch.to_pandas(types_mapper=None)
            for attack in chunk["Attack"].unique():
                if attack in samples_per_class:
                    needed = config.MAX_SAMPLES_PER_CLASS - len(samples_per_class[attack])
                else:
                    needed = config.MAX_SAMPLES_PER_CLASS
                if needed <= 0:
                    continue
                mask = chunk["Attack"] == attack
                attack_rows = chunk[mask]
                take = min(len(attack_rows), needed)
                if attack not in samples_per_class:
                    samples_per_class[attack] = attack_rows.iloc[:take]
                else:
                    samples_per_class[attack] = pd.concat([samples_per_class[attack], attack_rows.iloc[:take]], ignore_index=True)
                if len(samples_per_class[attack]) >= config.MAX_SAMPLES_PER_CLASS:
                    samples_per_class[attack] = samples_per_class[attack].iloc[:config.MAX_SAMPLES_PER_CLASS]
                if needed < len(attack_rows):
                    print(f"  {attack:<18} capped at {config.MAX_SAMPLES_PER_CLASS:,}")
        df = pd.concat(list(samples_per_class.values()), ignore_index=True).sample(frac=1, random_state=config.RANDOM_STATE).reset_index(drop=True)
    else:
        print("Downloading dataset from KaggleHub...")
        try:
            import kagglehub
            path = kagglehub.dataset_download(config.DATASET_SOURCE)
            df = pd.read_parquet(os.path.join(path, config.DATASET_FILE))
            df.to_parquet(dataset_path, index=False)
            print(f"Cached to {dataset_path}")
        except Exception as e:
            print(f"KaggleHub download failed: {e}")
            print(f"Place the dataset at: {dataset_path}")
            sys.exit(1)
    print(f"Dataset shape: {df.shape}")
    return df


def explore_dataset(df):
    print(f"\n{'='*60}\nDataset Exploration\n{'='*60}")
    print(f"Shape       : {df.shape}")
    print(f"Columns     : {list(df.columns)[:10]}... ({len(df.columns)} total)")
    print(f"Memory      : {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    print(f"Attack distribution:\n{df['Attack'].value_counts()}")
    print(f"Unique attack classes: {df['Attack'].nunique()}")


def balance_dataset(df):
    print(f"\n{'='*60}\nBalancing Dataset\n{'='*60}")
    balanced = []
    for attack in sorted(df["Attack"].unique()):
        attack_df = df[df["Attack"] == attack]
        sample_size = min(len(attack_df), config.MAX_SAMPLES_PER_CLASS)
        sampled = attack_df.sample(n=sample_size, random_state=config.RANDOM_STATE)
        balanced.append(sampled)
        print(f"  {attack:<18} {sample_size:>6,} samples")
    df_balanced = pd.concat(balanced).sample(frac=1, random_state=config.RANDOM_STATE).reset_index(drop=True)
    print(f"\nBalanced shape: {df_balanced.shape}")
    return df_balanced


def main():
    setup_environment()

    df = load_dataset()
    explore_dataset(df)

    X = df.drop(columns=["Attack", "Label"])
    y = df["Attack"]

    y_encoded, label_encoder = encode_labels(y, fit=True)
    class_names = label_encoder.classes_
    num_classes = len(class_names)
    print(f"Classes: {num_classes} {list(class_names)}")

    X_scaled, scaler = preprocess_features(X, fit=True)
    input_dim = X_scaled.shape[1]
    print(f"Input features: {input_dim}")

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=config.TEST_SPLIT, stratify=y_encoded, random_state=config.SEED)
    print(f"Split: train={len(X_train):,}  test={len(X_test):,}")

    clients, client_sizes = create_clients(X_train, y_train)
    print(f"Federated clients: {len(clients)}")

    global_model = create_model(input_dim, num_classes)
    global_model.summary()

    print(f"Training: {config.GLOBAL_ROUNDS} rounds, {config.EPOCHS_PER_CLIENT} epochs/client, {config.NUM_CLIENTS} clients, lr={config.LEARNING_RATE}")
    result = federated_training_loop(global_model, clients, client_sizes, X_test, y_test, input_dim, num_classes, verbose=True)

    eval_results = evaluate_model(result["model"], X_test, y_test, class_names, history=result["history"])

    save_preprocessing_artifacts(scaler, label_encoder)
    print(f"Best model: {config.BEST_MODEL_PATH}")
    print(f"Final model: {config.MODEL_PATH}")

    summary = {
        "best_accuracy": result["best_accuracy"],
        "test_accuracy": eval_results["test_accuracy"],
        "test_loss": eval_results["test_loss"],
        "input_dim": int(input_dim),
        "num_classes": int(num_classes),
        "class_names": list(class_names),
        "config": {"global_rounds": config.GLOBAL_ROUNDS, "local_epochs": config.EPOCHS_PER_CLIENT, "num_clients": config.NUM_CLIENTS, "batch_size": config.BATCH_SIZE, "learning_rate": config.LEARNING_RATE, "architecture": config.DENSE_UNITS},
    }
    with open(config.RESULTS_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'#'*60}\nTraining Complete!\nBest Accuracy: {result['best_accuracy']:.4f}\nTest Accuracy: {eval_results['test_accuracy']:.4f}\n{'#'*60}")


if __name__ == "__main__":
    main()
