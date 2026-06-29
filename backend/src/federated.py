import numpy as np
import tensorflow as tf

from src.model import create_model, get_client_callbacks
import config


def create_clients(X_train, y_train, num_clients=None):
    if num_clients is None:
        num_clients = config.NUM_CLIENTS

    indices = np.random.permutation(len(X_train))
    X_shuffled = X_train[indices]
    y_shuffled = y_train[indices]

    X_clients = np.array_split(X_shuffled, num_clients)
    y_clients = np.array_split(y_shuffled, num_clients)

    clients = list(zip(X_clients, y_clients))
    client_sizes = [len(x) for x in X_clients]

    return clients, client_sizes


def weighted_fed_average(client_weights, client_sizes):
    total_samples = sum(client_sizes)
    averaged_weights = []

    for layer_weights in zip(*client_weights):
        weighted = np.zeros_like(layer_weights[0])
        for weights, size in zip(layer_weights, client_sizes):
            weighted += weights * (size / total_samples)
        averaged_weights.append(weighted)

    return averaged_weights


def train_client(global_weights, X_client, y_client, input_dim, num_classes):
    client_model = create_model(input_dim, num_classes)
    client_model.set_weights(global_weights)

    client_model.fit(X_client, y_client, epochs=config.EPOCHS_PER_CLIENT, batch_size=config.BATCH_SIZE, callbacks=get_client_callbacks(), verbose=0)

    loss, accuracy = client_model.evaluate(X_client, y_client, batch_size=config.BATCH_SIZE, verbose=0)
    weights = client_model.get_weights()

    for w in weights:
        if np.isnan(w).any() or np.isinf(w).any():
            return None

    return {"weights": weights, "loss": float(loss), "accuracy": float(accuracy), "samples": len(X_client)}


def federated_training_loop(global_model, clients, client_sizes, X_test, y_test, input_dim, num_classes, global_rounds=None, verbose=True):
    if global_rounds is None:
        global_rounds = config.GLOBAL_ROUNDS

    global_weights = global_model.get_weights()
    best_accuracy = 0.0

    history = {"global_accuracy": [], "global_loss": [], "client_accuracy": [], "client_loss": []}

    for round_num in range(1, global_rounds + 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Global Round {round_num}/{global_rounds}")
            print(f"{'='*60}")

        client_results = []

        for client_id, (X_c, y_c) in enumerate(clients):
            result = train_client(global_weights, X_c, y_c, input_dim, num_classes)
            if result is None:
                if verbose:
                    print(f"  Client {client_id+1:02d}: SKIPPED (invalid weights)")
                continue
            client_results.append(result)
            if verbose:
                print(f"  Client {client_id+1:02d}: loss={result['loss']:.4f}  acc={result['accuracy']:.4f}")

        if not client_results:
            if verbose:
                print("No valid clients this round. Stopping.")
            break

        new_weights = weighted_fed_average([r["weights"] for r in client_results], [r["samples"] for r in client_results])

        invalid = any(np.isnan(w).any() or np.isinf(w).any() for w in new_weights)
        if invalid:
            if verbose:
                print("Invalid aggregated weights. Skipping round.")
            continue

        global_weights = new_weights
        global_model.set_weights(global_weights)

        global_loss, global_accuracy = global_model.evaluate(X_test, y_test, batch_size=config.BATCH_SIZE, verbose=0)
        avg_client_loss = float(np.mean([r["loss"] for r in client_results]))
        avg_client_acc = float(np.mean([r["accuracy"] for r in client_results]))

        history["global_loss"].append(global_loss)
        history["global_accuracy"].append(global_accuracy)
        history["client_loss"].append(avg_client_loss)
        history["client_accuracy"].append(avg_client_acc)

        if verbose:
            print(f"\n  Round Summary:")
            print(f"    Avg Client Accuracy: {avg_client_acc:.4f}")
            print(f"    Avg Client Loss    : {avg_client_loss:.4f}")
            print(f"    Global Accuracy    : {global_accuracy:.4f}")
            print(f"    Global Loss        : {global_loss:.4f}")

        if global_accuracy > best_accuracy:
            best_accuracy = global_accuracy
            global_model.save(str(config.BEST_MODEL_PATH))
            if verbose:
                print(f"    ** New best model saved ({best_accuracy:.4f})")

    if verbose:
        print(f"\n{'='*60}")
        print(f"Federated Training Complete — Best Accuracy: {best_accuracy:.4f}")

    global_model.save(str(config.MODEL_PATH))

    return {"model": global_model, "history": history, "best_accuracy": best_accuracy}
