import numpy as np
import tensorflow as tf

from src.model import create_model, get_client_callbacks
import config


def create_clients(X_train, y_train, num_clients=None, partition=None, alpha=None, seed=None):
    """Simulated partitions. IID is the baseline; non-IID options expose heterogeneity.

    partition: 'iid' (default), 'label_skew' (Dirichlet alpha), 'quantity_skew'.
    Returns (clients, client_sizes). Callers should log client_label_histogram().
    """
    if num_clients is None:
        num_clients = config.NUM_CLIENTS
    if partition is None:
        partition = getattr(config, "CLIENT_PARTITION", "iid")
    if alpha is None:
        alpha = getattr(config, "DIRICHLET_ALPHA", 0.5)
    rng = np.random.default_rng(seed if seed is not None else config.SEED)
    y_train = np.asarray(y_train)

    if partition == "iid":
        indices = rng.permutation(len(X_train))
        X_shuffled = X_train[indices]
        y_shuffled = y_train[indices]
        X_clients = np.array_split(X_shuffled, num_clients)
        y_clients = np.array_split(y_shuffled, num_clients)
    elif partition == "quantity_skew":
        # Same class mix, very different client sizes (Dirichlet over counts).
        proportions = rng.dirichlet([alpha] * num_clients)
        proportions = proportions / proportions.sum()
        counts = (proportions * len(X_train)).astype(int)
        counts[-1] += len(X_train) - counts.sum()  # fix rounding
        indices = rng.permutation(len(X_train))
        X_clients, y_clients = [], []
        start = 0
        for c in counts:
            idx = indices[start:start + max(0, int(c))]
            X_clients.append(X_train[idx] if len(idx) else np.empty((0,) + X_train.shape[1:]))
            y_clients.append(y_train[idx] if len(idx) else np.empty((0,), dtype=y_train.dtype))
            start += int(c)
    elif partition == "label_skew":
        # Dirichlet per-class mixing: clients get different attack prevalence.
        classes = np.unique(y_train)
        per_class_idx = {c: rng.permutation(np.where(y_train == c)[0]) for c in classes}
        client_indices: list[list] = [[] for _ in range(num_clients)]
        for c in classes:
            idx = per_class_idx[c]
            props = rng.dirichlet([alpha] * num_clients)
            counts = (props * len(idx)).astype(int)
            counts[-1] += len(idx) - counts.sum()
            start = 0
            for i, cnt in enumerate(counts):
                client_indices[i].extend(idx[start:start + int(cnt)].tolist())
                start += int(cnt)
        X_clients, y_clients = [], []
        for inds in client_indices:
            inds = np.array(inds, dtype=int)
            if len(inds) == 0:
                X_clients.append(np.empty((0,) + X_train.shape[1:]))
                y_clients.append(np.empty((0,), dtype=y_train.dtype))
            else:
                rng.shuffle(inds)
                X_clients.append(X_train[inds])
                y_clients.append(y_train[inds])
    else:
        raise ValueError(f"Unknown partition '{partition}'. Use iid/label_skew/quantity_skew.")

    clients = list(zip(X_clients, y_clients))
    client_sizes = [len(x) for x in X_clients]
    return clients, client_sizes


def client_label_histogram(y_clients, num_classes=None):
    """Per-client label counts for run metadata (no raw data leaves the site in real FL)."""
    hist = []
    for y in y_clients:
        y = np.asarray(y)
        if num_classes is None:
            uniq, counts = np.unique(y, return_counts=True)
            hist.append({int(k): int(v) for k, v in zip(uniq, counts)})
        else:
            hist.append({int(c): int(np.sum(y == c)) for c in range(num_classes)})
    return hist


def weighted_fed_average(client_weights, client_sizes):
    if not client_weights or not client_sizes:
        raise ValueError("No client updates to aggregate.")
    if len(client_weights) != len(client_sizes):
        raise ValueError("client_weights and client_sizes length mismatch.")
    total_samples = sum(client_sizes)
    if total_samples <= 0:
        raise ValueError("Total client samples must be positive.")
    for s in client_sizes:
        if s <= 0:
            raise ValueError("Client sample counts must be positive.")
    ref_len = len(client_weights[0])
    ref_shapes = [w.shape for w in client_weights[0]]
    for i, weights in enumerate(client_weights):
        if len(weights) != ref_len:
            raise ValueError(f"Client {i}: layer count mismatch.")
        for j, w in enumerate(weights):
            w = np.asarray(w)
            if w.shape != ref_shapes[j]:
                raise ValueError(f"Client {i} layer {j}: shape {w.shape} != {ref_shapes[j]}.")
            if not np.all(np.isfinite(w)):
                raise ValueError(f"Client {i} layer {j}: non-finite values.")
            norm = float(np.linalg.norm(w.ravel()))
            if norm > config.MAX_UPDATE_NORM * max(1.0, np.sqrt(w.size)):
                raise ValueError(f"Client {i} layer {j}: update norm {norm:.1f} exceeds bound.")

    averaged_weights = []

    for layer_weights in zip(*client_weights):
        weighted = np.zeros_like(np.asarray(layer_weights[0], dtype=np.float64))
        for weights, size in zip(layer_weights, client_sizes):
            weighted += np.asarray(weights, dtype=np.float64) * (size / total_samples)
        averaged_weights.append(weighted)

    return averaged_weights


def update_delta_norm(new_weights, global_weights):
    """L2 norm of the model-update delta (new - global), the quantity a
    norm guard must bound — not the raw parameter norm."""
    total = 0.0
    for w_new, w_old in zip(new_weights, global_weights):
        d = np.asarray(w_new, dtype=np.float64) - np.asarray(w_old, dtype=np.float64)
        total += float(np.sum(d * d))
    return float(np.sqrt(total))


def validate_client_update(new_weights, global_weights, max_norm=None):
    """Reject non-finite or over-norm *deltas*. Returns delta norm."""
    if max_norm is None:
        max_norm = config.MAX_UPDATE_NORM
    if len(new_weights) != len(global_weights):
        raise ValueError("Update layer count mismatch.")
    for j, (w_new, w_old) in enumerate(zip(new_weights, global_weights)):
        w_new = np.asarray(w_new)
        if np.asarray(w_old).shape != w_new.shape:
            raise ValueError(f"Update layer {j}: shape mismatch.")
        if not np.all(np.isfinite(w_new)):
            raise ValueError(f"Update layer {j}: non-finite values.")
    norm = update_delta_norm(new_weights, global_weights)
    if not np.isfinite(norm):
        raise ValueError("Update delta norm is non-finite.")
    if norm > max_norm:
        raise ValueError(f"Update delta norm {norm:.1f} exceeds bound {max_norm}.")
    return norm


def compute_class_weights(y):
    classes = np.unique(y)
    n_samples = len(y)
    n_classes = len(classes)
    weights = {}
    for cls in classes:
        n_cls = int(np.sum(y == cls))
        weights[int(cls)] = n_samples / (float(n_classes) * float(n_cls))
    return weights


def train_client(global_weights, X_client, y_client, input_dim, num_classes, class_weight=None):
    client_model = create_model(input_dim, num_classes)
    client_model.set_weights(global_weights)

    client_model.fit(X_client, y_client, epochs=config.EPOCHS_PER_CLIENT, batch_size=config.BATCH_SIZE, callbacks=get_client_callbacks(), class_weight=class_weight, verbose=0)

    loss, accuracy = client_model.evaluate(X_client, y_client, batch_size=config.BATCH_SIZE, verbose=0)
    weights = client_model.get_weights()

    for w in weights:
        if np.isnan(w).any() or np.isinf(w).any():
            return None
    try:
        delta_norm = validate_client_update(weights, global_weights)
    except ValueError:
        return None

    return {"weights": weights, "loss": float(loss), "accuracy": float(accuracy), "samples": len(X_client), "delta_norm": float(delta_norm)}


def federated_training_loop(global_model, clients, client_sizes, X_val, y_val, input_dim, num_classes, global_rounds=None, verbose=True, best_model_path=None, final_model_path=None, class_weight=None, X_test=None, y_test=None, client_fraction=None, min_clients=None, seed=None):
    if global_rounds is None:
        global_rounds = config.GLOBAL_ROUNDS
    if best_model_path is None:
        best_model_path = config.CICIOT2023_BEST_PATH
    if final_model_path is None:
        final_model_path = config.CICIOT2023_MODEL_PATH
    if client_fraction is None:
        client_fraction = getattr(config, "CLIENT_FRACTION", 1.0)
    if min_clients is None:
        min_clients = getattr(config, "MIN_CLIENTS", 1)
    rng = np.random.default_rng(seed if seed is not None else config.SEED)

    global_weights = global_model.get_weights()
    best_accuracy = 0.0

    history = {"global_accuracy": [], "global_loss": [], "client_train_accuracy": [], "client_train_loss": [],
               # backward-compat aliases
               "client_accuracy": [], "client_loss": [],
               "val_accuracy": [], "val_loss": [],
               "participating_clients": [], "comm_bytes_upload": []}

    num_available = len(clients)
    per_round = max(int(min_clients), int(round(num_available * client_fraction)))
    per_round = max(1, min(num_available, per_round))

    for round_num in range(1, global_rounds + 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"Global Round {round_num}/{global_rounds}")
            print(f"{'='*60}")

        client_results = []

        # Partial participation: sample a reproducible subset per round so
        # dropout tolerance is measurable instead of assumed.
        round_idx = rng.permutation(num_available)[:per_round]
        if verbose and per_round < num_available:
            print(f"  Participation: {per_round}/{num_available} clients sampled")

        for client_id in [int(i) for i in round_idx]:
            X_c, y_c = clients[client_id]
            if len(X_c) == 0:
                if verbose:
                    print(f"  Client {client_id+1:02d}: SKIPPED (empty partition)")
                continue
            try:
                result = train_client(global_weights, X_c, y_c, input_dim, num_classes, class_weight=class_weight)
            except Exception as e:
                if verbose:
                    print(f"  Client {client_id+1:02d}: SKIPPED ({type(e).__name__}: {e})")
                continue
            if result is None:
                if verbose:
                    print(f"  Client {client_id+1:02d}: SKIPPED (invalid weights)")
                continue
            client_results.append(result)
            if verbose:
                print(f"  Client {client_id+1:02d}: loss={result['loss']:.4f}  acc={result['accuracy']:.4f}")

        if len(client_results) < min_clients:
            if verbose:
                print(f"Only {len(client_results)} valid clients (< min {min_clients}). Skipping round.")
            history["participating_clients"].append(0)
            history["comm_bytes_upload"].append(0)
            continue

        if not client_results:
            if verbose:
                print("No valid clients this round. Stopping.")
            break

        try:
            new_weights = weighted_fed_average([r["weights"] for r in client_results], [r["samples"] for r in client_results])
        except ValueError as e:
            if verbose:
                print(f"Invalid client updates, skipping round: {e}")
            continue

        invalid = any(np.isnan(w).any() or np.isinf(w).any() for w in new_weights)
        if invalid:
            if verbose:
                print("Invalid aggregated weights. Skipping round.")
            continue

        global_weights = new_weights
        global_model.set_weights(global_weights)

        # Validation-only checkpoint selection. The held-out test set must
        # never be touched inside this loop (audit P0).
        global_loss, global_accuracy = global_model.evaluate(X_val, y_val, batch_size=config.BATCH_SIZE, verbose=0)
        avg_client_loss = float(np.mean([r["loss"] for r in client_results]))
        avg_client_acc = float(np.mean([r["accuracy"] for r in client_results]))

        history["global_loss"].append(global_loss)
        history["global_accuracy"].append(global_accuracy)
        history["val_loss"].append(global_loss)
        history["val_accuracy"].append(global_accuracy)
        history["client_train_loss"].append(avg_client_loss)
        history["client_train_accuracy"].append(avg_client_acc)
        history["client_loss"].append(avg_client_loss)
        history["client_accuracy"].append(avg_client_acc)
        history["participating_clients"].append(len(client_results))
        history["comm_bytes_upload"].append(int(sum(
            sum(np.asarray(w).nbytes for w in r["weights"]) for r in client_results)))

        if verbose:
            print(f"\n  Round Summary (client metrics = TRAIN metrics):")
            print(f"    Avg Client Train Accuracy: {avg_client_acc:.4f}")
            print(f"    Avg Client Train Loss    : {avg_client_loss:.4f}")
            print(f"    Global Val Accuracy      : {global_accuracy:.4f}")
            print(f"    Global Val Loss          : {global_loss:.4f}")

        if global_accuracy > best_accuracy:
            best_accuracy = global_accuracy
            global_model.save(str(best_model_path))
            if verbose:
                print(f"    ** New best model saved ({best_accuracy:.4f})")

    if verbose:
        print(f"\n{'='*60}")
        print(f"Federated Training Complete — Best Accuracy: {best_accuracy:.4f}")

    global_model.save(str(final_model_path))

    return {"model": global_model, "history": history, "best_accuracy": best_accuracy}
