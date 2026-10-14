import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (classification_report, confusion_matrix,
                             ConfusionMatrixDisplay, f1_score, precision_recall_fscore_support,
                             balanced_accuracy_score, roc_auc_score)
import warnings

import config


def expected_calibration_error(y_true, y_prob, n_bins=15):
    """ECE over max-probability bins. Softmax scores are not calibrated probs."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (confidences > lo) & (confidences <= hi)
        if np.any(mask):
            ece += abs(float(np.mean(accuracies[mask])) - float(np.mean(confidences[mask]))) * float(np.mean(mask))
    return float(ece)


def benign_false_positive_rate(y_true, y_pred, class_names):
    """One-vs-rest FPR with benign as the negative class, when identifiable."""
    names = [str(c).lower() for c in class_names]
    if "benign" not in names:
        return None
    benign_idx = names.index("benign")
    y_true_bin = (np.asarray(y_true) != benign_idx).astype(int)  # 1 = attack
    y_pred_bin = (np.asarray(y_pred) != benign_idx).astype(int)
    fp = int(np.sum((y_pred_bin == 1) & (y_true_bin == 0)))
    tn = int(np.sum((y_pred_bin == 0) & (y_true_bin == 0)))
    if fp + tn == 0:
        return None
    return float(fp / (fp + tn))


def evaluate_model(model, X_test, y_test, class_names, history=None, save_dir=None):
    from pathlib import Path as _Path
    if save_dir is None:
        save_dir = config.RESULTS_DIR
    save_dir = _Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    test_loss, test_accuracy = model.evaluate(X_test, y_test, batch_size=config.BATCH_SIZE, verbose=1)
    print(f"Test Accuracy: {test_accuracy:.4f} | Test Loss: {test_loss:.4f}")

    y_pred_probs = model.predict(X_test, batch_size=config.BATCH_SIZE, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)

    report = classification_report(y_test, y_pred, target_names=class_names, digits=4, output_dict=True)
    print(classification_report(y_test, y_pred, target_names=class_names, digits=4))

    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    balanced_acc = float(balanced_accuracy_score(y_test, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, zero_division=0)
    per_class = {str(c): {"precision": float(p), "recall": float(r), "f1": float(f)}
                 for c, p, r, f in zip(class_names, prec, rec, f1)}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            roc_auc_macro = float(roc_auc_score(y_test, y_pred_probs, multi_class="ovr", average="macro"))
    except Exception:
        roc_auc_macro = None
    ece = expected_calibration_error(y_test, y_pred_probs)
    benign_fpr = benign_false_positive_rate(y_test, y_pred, class_names)
    print(f"Macro-F1: {macro_f1:.4f} | Balanced-acc: {balanced_acc:.4f} | ECE: {ece:.4f}"
          + (f" | Benign-FPR: {benign_fpr:.4f}" if benign_fpr is not None else ""))

    fig, ax = plt.subplots(figsize=(12, 10))
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, cmap="Blues", values_format="d", xticks_rotation=45)
    ax.set_title("Confusion Matrix — AIPFL-IDS")
    plt.tight_layout()
    plt.savefig(str(save_dir / "confusion_matrix.png"), dpi=150)
    plt.close()

    if history is not None:
        plot_training_history(history, save_dir)

    metrics = {"test_accuracy": float(test_accuracy), "test_loss": float(test_loss),
               "classification_report": report, "macro_f1": macro_f1,
               "balanced_accuracy": balanced_acc, "per_class": per_class,
               "roc_auc_macro_ovr": roc_auc_macro, "ece": ece,
               "benign_fpr": benign_fpr}
    # Persist machine-readable metrics for dashboard/CI (no invented values).
    try:
        import json
        with open(str(save_dir / "test_metrics.json"), "w") as f:
            json.dump({k: v for k, v in metrics.items() if k != "classification_report"}, f, indent=2)
    except Exception:
        pass
    return metrics


def plot_training_history(history, save_dir=None):
    if save_dir is None:
        save_dir = config.RESULTS_DIR

    epochs = range(1, len(history["global_accuracy"]) + 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epochs, history["global_accuracy"], "o-", linewidth=2, label="Global Accuracy")
    ax.plot(epochs, history["client_accuracy"], "s--", linewidth=1.5, label="Avg Client Accuracy")
    ax.set_title("Model Accuracy vs Communication Rounds")
    ax.set_xlabel("Global Round")
    ax.set_ylabel("Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(str(save_dir / "accuracy_plot.png"), dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epochs, history["global_loss"], "o-", linewidth=2, color="red", label="Global Loss")
    ax.plot(epochs, history["client_loss"], "s--", linewidth=1.5, color="orange", label="Avg Client Loss")
    ax.set_title("Model Loss vs Communication Rounds")
    ax.set_xlabel("Global Round")
    ax.set_ylabel("Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(str(save_dir / "loss_plot.png"), dpi=150)
    plt.close()
