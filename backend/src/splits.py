"""Data-splitting contracts shared by training and baselines.

TF-free on purpose: `train.py` and `baselines.py` both split the *raw* rows
before any preprocessing is fitted, and the test suite imports this module
without pulling TensorFlow into CI.
"""

import config


def stratified_splits(X_raw, y_raw, seed=None):
    """Raw-first stratified train/val/test split.

    Shared with baselines.py so centralized baselines are measured on the
    exact same rows as the federated run. Preprocessing is NOT fitted here —
    callers fit on train only.
    """
    from sklearn.model_selection import train_test_split
    seed = config.SEED if seed is None else seed
    try:
        X_tr_df, X_te_df, y_tr, y_te = train_test_split(
            X_raw, y_raw, test_size=config.TEST_SPLIT,
            stratify=y_raw, random_state=seed)
        val_frac = config.VALIDATION_SPLIT / (1.0 - config.TEST_SPLIT)
        X_tr_df, X_va_df, y_tr, y_va = train_test_split(
            X_tr_df, y_tr, test_size=val_frac, stratify=y_tr, random_state=seed)
    except ValueError:
        # Fallback for degenerate tiny/rare-class samples.
        X_tr_df, X_te_df, y_tr, y_te = train_test_split(
            X_raw, y_raw, test_size=config.TEST_SPLIT, random_state=seed)
        val_frac = config.VALIDATION_SPLIT / (1.0 - config.TEST_SPLIT)
        X_tr_df, X_va_df, y_tr, y_va = train_test_split(
            X_tr_df, y_tr, test_size=val_frac, random_state=seed)
    return X_tr_df, X_va_df, X_te_df, y_tr, y_va, y_te
