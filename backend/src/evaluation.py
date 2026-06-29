import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

import config


def evaluate_model(model, X_test, y_test, class_names, history=None, save_dir=None):
    if save_dir is None:
        save_dir = config.RESULTS_DIR

    test_loss, test_accuracy = model.evaluate(X_test, y_test, batch_size=config.BATCH_SIZE, verbose=1)
    print(f"Test Accuracy: {test_accuracy:.4f} | Test Loss: {test_loss:.4f}")

    y_pred_probs = model.predict(X_test, batch_size=config.BATCH_SIZE, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)

    report = classification_report(y_test, y_pred, target_names=class_names, digits=4, output_dict=True)
    print(classification_report(y_test, y_pred, target_names=class_names, digits=4))

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

    return {"test_accuracy": float(test_accuracy), "test_loss": float(test_loss), "classification_report": report}


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
