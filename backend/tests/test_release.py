"""Release verification: mismatch refused, missing manifest warns (P0 #2)."""
import importlib.util
import sys
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import config  # noqa: E402

PKG = types.ModuleType("src")
PKG.__path__ = [str(BACKEND / "src")]
sys.modules.setdefault("src", PKG)


def _load(name):
    spec = importlib.util.spec_from_file_location(
        f"src.{name}", str(BACKEND / "src" / f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"src.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_verify_accepts_matching(tmp_path):
    rel = _load("release")
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"model-bytes")
    b.write_bytes(b"scaler-bytes")
    import hashlib
    import json
    manifest = {"artifact_sha256": {
        "a.bin": hashlib.sha256(b"model-bytes").hexdigest(),
        "b.bin": hashlib.sha256(b"scaler-bytes").hexdigest(),
    }}
    (tmp_path / "release_DS.json").write_text(json.dumps(manifest))
    out = rel.verify_release("DS", str(a), str(tmp_path / "missing1"),
                             str(tmp_path / "missing2"), str(b), tmp_path)
    assert out["artifact_sha256"]["a.bin"].startswith(manifest["artifact_sha256"]["a.bin"][:8])


def test_verify_rejects_tampered(tmp_path):
    rel = _load("release")
    a = tmp_path / "a.bin"
    a.write_bytes(b"original")
    import hashlib
    import json
    manifest = {"artifact_sha256": {"a.bin": hashlib.sha256(b"original").hexdigest()}}
    (tmp_path / "release_DS.json").write_text(json.dumps(manifest))
    a.write_bytes(b"tampered")
    try:
        rel.verify_release("DS", str(a), str(tmp_path / "m1"),
                           str(tmp_path / "m2"), str(tmp_path / "m3"), tmp_path)
    except ValueError:
        return
    raise AssertionError("tampered artifact must be refused")


def test_verify_missing_manifest_warns(tmp_path):
    rel = _load("release")
    out = rel.verify_release("DS", str(tmp_path / "a"), str(tmp_path / "b"),
                             str(tmp_path / "c"), str(tmp_path / "d"), tmp_path)
    assert "warning" in out


def _write_manifest(tmp_path, dataset, digests):
    import json
    (tmp_path / f"release_{dataset}.json").write_text(
        json.dumps({"dataset": dataset, "artifact_sha256": digests}))


def test_strict_rejects_incomplete_manifest(tmp_path):
    import hashlib
    rel = _load("release")
    a = tmp_path / "m.bin"
    a.write_bytes(b"x")
    _write_manifest(tmp_path, "DS", {"m.bin": hashlib.sha256(b"x").hexdigest()})
    try:
        rel.verify_release("DS", str(a), str(tmp_path / "s"),
                           str(tmp_path / "e"), str(tmp_path / "f"),
                           tmp_path, require_manifest=True)
    except ValueError as e:
        assert "Incomplete" in str(e)
        return
    raise AssertionError("incomplete manifest must fail in strict mode")


def test_strict_rejects_dataset_mismatch(tmp_path):
    import hashlib
    import json
    rel = _load("release")
    a = tmp_path / "m.bin"
    a.write_bytes(b"x")
    (tmp_path / "release_DS.json").write_text(json.dumps(
        {"dataset": "OTHER",
         "artifact_sha256": {"m.bin": hashlib.sha256(b"x").hexdigest()}}))
    try:
        rel.verify_release("DS", str(a), str(tmp_path / "s"),
                           str(tmp_path / "e"), str(tmp_path / "f"),
                           tmp_path, require_manifest=True)
    except ValueError as e:
        assert "dataset" in str(e).lower()
        return
    raise AssertionError("dataset mismatch must fail")


def test_strict_rejects_malformed_digest(tmp_path):
    rel = _load("release")
    a = tmp_path / "m.bin"
    a.write_bytes(b"x")
    _write_manifest(tmp_path, "DS", {
        "m.bin": "not-a-hash",
        "s": "0" * 64, "e": "1" * 64, "f": "2" * 64})
    try:
        rel.verify_release("DS", str(a), str(tmp_path / "s"),
                           str(tmp_path / "e"), str(tmp_path / "f"),
                           tmp_path, require_manifest=True)
    except ValueError as e:
        assert "Malformed" in str(e)
        return
    raise AssertionError("malformed digest must fail")
