"""Release manifest verification (P0 #2).

train.py writes backend/results/release_<dataset>.json with sha256 per
artifact. PredictService verifies the files it is about to deserialize
against that manifest when present. A manifest colocated with mutable
files is integrity evidence, not a trust signature — see docs/THREAT_MODEL.md.
"""
import hashlib
import json
import os


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _strict_mode(require_manifest):
    return bool(require_manifest) or os.environ.get("AIPFL_REQUIRE_MANIFEST") == "1"


def verify_release(dataset, model_path, scaler_path, encoder_path, feature_path,
                   results_dir, require_manifest=False):
    """Verify all four required artifacts against the release manifest.

    Strict mode (require_manifest=True or AIPFL_REQUIRE_MANIFEST=1, required
    for production): manifest must exist, name the dataset, and carry a
    valid sha256 for every required artifact. Non-strict mode preserves the
    old behavior for pre-manifest local runs: warn and continue when the
    manifest is absent, but still refuse any listed hash that mismatches.
    """
    import re
    import config
    strict = _strict_mode(require_manifest)
    manifest_path = (results_dir or config.RESULTS_DIR) / f"release_{dataset}.json"
    if not os.path.exists(manifest_path):
        if strict:
            raise FileNotFoundError(
                f"Release manifest missing: {manifest_path}. Retrain to generate a verified release.")
        return {"warning": "no release manifest; loaded without hash verification"}
    with open(manifest_path) as f:
        manifest = json.load(f)
    if manifest.get("dataset") and manifest["dataset"] != dataset:
        raise ValueError(
            f"Manifest dataset '{manifest['dataset']}' does not match '{dataset}'.")
    expected = (manifest.get("artifact_sha256") or {})
    required_bases = {os.path.basename(str(p)) for p in
                      [model_path, scaler_path, encoder_path, feature_path]}
    if strict:
        missing = sorted(required_bases - set(expected))
        if missing:
            raise ValueError(
                f"Incomplete release manifest: missing hash(es) for {missing}.")
    for base, digest in expected.items():
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest or "")):
            raise ValueError(f"Malformed sha256 for {base} in release manifest.")
    # Map by basename since manifest keys are basenames.
    by_base = {os.path.basename(str(p)): str(p) for p in
               [model_path, scaler_path, encoder_path, feature_path]}
    for base, digest in expected.items():
        actual_path = by_base.get(base)
        if not actual_path or not os.path.exists(actual_path):
            raise FileNotFoundError(f"Release artifact missing: {base}")
        actual = sha256_file(actual_path)
        if actual != digest:
            raise ValueError(
                f"Hash mismatch for {base}: manifest {digest[:12]}… != file {actual[:12]}…. "
                "Refusing to load a stale or tampered release.")
    if strict:
        manifest["_strict_verified"] = True
    return manifest
