"""CICIoT loader: case-insensitive label column + mixed-case labels + chunking.

Imports only the loader's AST from train.py so the suite never pulls
TensorFlow (same spirit as test_sampling.py's source-exec trick).
"""
import ast
import glob
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import config  # noqa: E402

_WANTED = {"merge_ciciot_classes", "resolve_label_col", "normalize_ciciot_labels",
           "load_ciciot2023"}


def _load_namespace():
    tree = ast.parse((BACKEND / "train.py").read_text(encoding="utf-8"))
    nodes = []
    for n in tree.body:
        if getattr(n, "name", None) in _WANTED:
            nodes.append(n)
        elif isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in (
                "CICIOT_CLASS_MAP", "CSV_CHUNK_ROWS"):
            nodes.append(n)
        elif isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "LAST_RAW_TOTALS":
            nodes.append(n)
    found = {getattr(n, "name", None) or getattr(n.targets[0] if isinstance(n, ast.Assign)
                                                 else n.target, "id", None) for n in nodes}
    missing = _WANTED - {f for f in found if f}
    assert not missing, f"train.py is missing loader symbols: {missing}"
    ns = {"os": os, "glob": glob, "pd": pd, "config": config, "__name__": "train_loader"}
    mod = ast.Module(body=nodes, type_ignores=[])
    exec(compile(mod, str(BACKEND / "train.py"), "exec"), ns)
    return ns


NS = _load_namespace()


def test_resolve_label_col_case_insensitive():
    got = NS["resolve_label_col"](["flow_duration", "label", "Rate"])
    assert got == "label"
    got2 = NS["resolve_label_col"](["flow_duration", "Label", "Rate"])
    assert got2 == "Label"
    with pytest.raises(ValueError, match="Columns present"):
        NS["resolve_label_col"](["flow_duration", "Rate"])


def test_normalize_merges_mixed_case_labels_and_filters_blanks():
    df = pd.DataFrame({"label": ["BenignTraffic", "benigntraffic", " DDoS-ACK_Fragmentation ",
                                 "nan", "", "DNS_Spoofing", "Recon-PingSweep"]})
    out = NS["normalize_ciciot_labels"](df, "label")
    assert list(out["label"]) == ["BENIGN", "BENIGN", "DDOS", "DNS_SPOOFING", "RECON"]


def test_load_ciciot2023_chunked_and_capped(tmp_path, monkeypatch):
    """Two mirror layouts (lowercase `label`, uppercase `Label`) in one glob."""
    d = tmp_path / "raw" / "CICIoT2023 mirror"
    d.mkdir(parents=True)
    # 30 benign + 3 DDoS rows split across two files, mixed case.
    pd.DataFrame({
        "flow_duration": range(20),
        "label": ["BenignTraffic"] * 15 + ["DDoS-ACK_Fragmentation"] * 3 + ["Recon-PingSweep"] * 2,
    }).to_csv(d / "part1.csv", index=False)
    pd.DataFrame({
        "flow_duration": range(20),
        "Label": ["BENIGNTRAFFIC"] * 15 + ["DDOS-ACK_FRAGMENTATION"] * 3 + ["DNS_SPOOFING"] * 2,
    }).to_csv(d / "part2.csv", index=False)

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "CICIOT2023_PATTERN", "raw/CICIoT2023*/*.csv")
    monkeypatch.setattr(config, "CICIOT2023_MAX_SAMPLES_PER_CLASS", 12)

    df = NS["load_ciciot2023"]()
    counts = df[config.CICIOT2023_LABEL_COL].value_counts().to_dict()
    # BENIGN merged from both spellings, capped at 12; small classes kept whole.
    assert counts["BENIGN"] == 12
    assert counts["DDOS"] == 6
    assert counts["DNS_SPOOFING"] == 2
    assert counts["RECON"] == 2
    assert set(df[config.CICIOT2023_LABEL_COL]) == {"BENIGN", "DDOS", "DNS_SPOOFING", "RECON"}
    # Raw totals recorded before capping (30 benign rows total).
    assert NS["LAST_RAW_TOTALS"]["BENIGN"] == 30
