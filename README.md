# AIPFL-IDS

**AI-Powered Federated Learning Intrusion Detection System**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](#)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)](#)
[![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)](#)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

Research-prototype cybersecurity platform using Deep Learning + simulated Federated Learning to detect malicious IoT network traffic. Client partitions are simulated in one process — this does not yet demonstrate privacy guarantees for independent clients, secure aggregation, or differential privacy (see `docs/THREAT_MODEL.md`). Supports **two datasets**: CICIoT2023 (34 original labels, mapped to 10 categories) and NF-ToN-IoT-V2 (10 classes).

---

## Architecture

```
frontend/ (Next.js :3000)        backend/ (Flask :5000)
/home  /about  /dashboard         POST /api/predict?dataset=
/predict  /contact                GET  /api/status
         |                             /api/health
         |  fetch /api/*               /api/models
         +-------- proxy ----------+  /api/config
                                        |
                                    src/ — ML Pipeline
                                    TensorFlow DNN 512→256→128→64→10/10
                                    Dual-model: separate scalers, encoders, models
                                    FedAvg, StandardScaler, LabelEncoder
```

---

## Project Structure

```
AIPFL-IDS/
├── frontend/                # Next.js (React, TypeScript)
│   ├── app/                 # App Router pages
│   │   ├── layout.tsx       # Root layout (Navbar, Footer, Theme)
│   │   ├── page.tsx         # Home page with dual-dataset metrics
│   │   ├── globals.css      # Design tokens, theme, animations
│   │   ├── about/           # About page
│   │   ├── dashboard/       # Live metrics dashboard (dual-dataset)
│   │   ├── predict/         # File upload with dataset selector
│   │   └── contact/         # Contact form
│   ├── components/          # Reusable React components
│   ├── lib/api.ts           # API client (fetch wrapper)
│   ├── package.json
│   ├── next.config.mjs      # API proxy /api/* -> :5000
│   └── tsconfig.json
│
├── backend/                 # Python Flask + ML
│   ├── server/
│   │   ├── app.py           # Flask API (dual-model, 12 routes)
│   │   └── requirements.txt
│   ├── src/                 # ML core
│   │   ├── model.py         # DNN architecture
│   │   ├── preprocessing.py # Feature engineering (clip_extreme, clean_infinite)
│   │   ├── federated.py     # FedAvg
│   │   ├── splits.py        # Raw-first train/val/test split (shared with baselines)
│   │   ├── evaluation.py    # Metrics, confusion matrix
│   │   ├── predict.py       # Dual-model prediction service
│   │   └── utils.py         # GPU, seeds, precision
│   ├── data/raw/            # Datasets (gitignored; see Datasets below)
│   ├── models/              # Both trained models + scalers + encoders (gitignored)
│   ├── uploads/             # Temporary prediction uploads
│   ├── results/             # Evaluation plots, training/baseline summaries (gitignored)
│   ├── config.py            # Hyperparameters, dual-dataset paths
│   ├── train.py             # Training pipeline (--dataset flag)
│   └── baselines.py         # Centralized baseline (rf|logreg) on the same split
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Quick Start

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.11+**
- **CUDA** (optional, for GPU training)

### Frontend
```bash
cd frontend
npm install
npm run dev          # -> http://localhost:3000
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python train.py --dataset CICIoT2023    # needs raw CSVs (see Datasets below)
python train.py --dataset NF-ToN-IoT-V2 # auto-downloads on first run
python server/app.py # -> http://localhost:5000
```
> No model is shipped in the repo. Without a training run the server still
> boots, but `/api/status` reports `model_loaded: false` and `/api/metrics`
> returns `null`.

### Run (two terminals)
**Terminal 1:** `cd frontend && npm run dev`
**Terminal 2:** `cd backend && python server/app.py`

Open `http://localhost:3000` -- Next.js proxies `/api/*` to Flask.

### Production Build
```bash
cd frontend
npm run build && npm start
```

---

## Training

```bash
cd backend
python train.py --dataset CICIoT2023    # 34 original labels mapped to 10 categories
python train.py --dataset NF-ToN-IoT-V2  # Balanced 50K/class, 10 classes
```

### Common Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `GLOBAL_ROUNDS` | 30 | Federated communication rounds |
| `NUM_CLIENTS` | 10 | Simulated clients |
| `EPOCHS_PER_CLIENT` | 5 | Local epochs per round |
| `BATCH_SIZE` | 1024 | Training batch size |
| `LEARNING_RATE` | 0.001 | Adam learning rate |
| `DENSE_UNITS` | [512,256,128] | Hidden layers |

### CICIoT2023 Results (release 2026-11-15)

Produced by the current leak-free pipeline: raw-first split, preprocessing fit
on train only, checkpoint selected on validation only, test evaluated once.
Full provenance (metrics, per-class F1, client histograms, sha256 manifest) in
`training_summary_CICIoT2023.json` and `release_CICIoT2023.json`.

| Metric | Value |
|--------|-------|
| Test Accuracy | **79.13%** |
| Macro-F1 | 68.24% |
| Balanced Accuracy | 66.72% |
| Expected Calibration Error | 0.71% |
| Benign FPR | 14.22% |
| Best Val Accuracy | 79.32% |
| Input Features | 42 |
| Attack Classes | 10 (merged from 34 original labels: DDOS, DOS, MIRAI, RECON, BENIGN, DICTIONARYBRUTEFORCE, DNS_SPOOFING, MITM-ARPSPOOFING, VULNERABILITYSCAN, OTHER) |
| Balanced Samples | 325,676 (train split 211,688, 50K max/class) |
| Raw Records | 6,668,822 (Kaggle mirror) |

### NF-ToN-IoT-V2 Results (release 2026-11-04)

| Metric | Value |
|--------|-------|
| Test Accuracy | **91.27%** |
| Macro-F1 | 88.62% |
| Balanced Accuracy | 87.43% |
| Expected Calibration Error | 0.83% |
| Benign FPR | 5.76% |
| Best Val Accuracy | 91.36% |
| Input Features | 41 |
| Attack Classes | 10 (Benign, DDoS, DoS, Injection, Ransomware, Scanning, XSS, Backdoor, Password, MITM) |
| Balanced Samples | 377,332 (train split 245,265, 50K max/class) |
| Raw Records | 13,135,881 |

### Centralized baselines (same split — `backend/baselines.py`)

| Dataset | Model | Test Acc | Macro-F1 |
|---------|-------|----------|----------|
| CICIoT2023 | FedAvg DNN (simulated, this repo) | 79.13% | 68.24% |
| CICIoT2023 | Random Forest (centralized) | 92.85% | 86.05% |
| CICIoT2023 | Logistic Regression (centralized) | 71.46% | 52.66% |
| NF-ToN-IoT-V2 | FedAvg DNN (simulated, this repo) | 91.27% | 88.62% |
| NF-ToN-IoT-V2 | Random Forest (centralized) | 94.08% | 91.90% |
| NF-ToN-IoT-V2 | Logistic Regression (centralized) | 79.04% | 76.98% |

Baselines use the identical raw-first split and preprocessing protocol, so the
comparison is apples-to-apples: FedAvg comfortably beats a linear model and
trails an ensemble of trees — the honest cost of averaging a small DNN across
10 simulated clients.

---

## Features

- **Dual-Dataset Architecture**: CICIoT2023 (34 original labels mapped to 10 categories) and NF-ToN-IoT-V2 (10 classes), with separate scalers, encoders, and models
- **Robust Preprocessing**: `clip_extreme()` handles extreme byte-rate features (up to 1e+261) using percentile-based clipping
- **Streaming Batch Loading**: 400K-row chunks for memory-efficient processing of the 6.67M-row CICIoT2023 raw CSVs
- **Federated Averaging (FedAvg)**: 10 simulated clients, weighted aggregation, configurable rounds/epochs, IID or Dirichlet non-IID partitions
- **Dual-Model API**: Select dataset via `?dataset=CICIoT2023` or `?dataset=NF-ToN-IoT-V2` query parameter
- **Bold UI**: high-contrast yellow/blue identity, subtle borders, consistent 8–12px radii, keyboard focus states, reduced-motion support

---

## API Reference

All endpoints at `/api/*` (proxied to Flask). Response format: `{success: bool, data?: ..., error?: string}`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict?dataset=` | POST | Upload CSV/Parquet file -> predictions (sync, bounded rows/cols) |
| `/api/predict-batch?dataset=` | POST | JSON `{features: [...]}` -> predictions (capped rows) |
| `/api/jobs?dataset=` | POST | Upload file -> 202 + `job_id` (background, same bounds) |
| `/api/jobs/<job_id>` | GET | Job status/summary (no full row dump) |
| `/api/jobs/<job_id>/download` | GET | Result CSV download when done |
| `/api/status` | GET | Server + both models status |
| `/api/health` | GET | Process liveness + uptime (not readiness) |
| `/api/livez` | GET | Process liveness only |
| `/api/readyz` | GET | 200 only when model + preprocessor + dry-run pass; 503 otherwise |
| `/api/metrics` | GET | Persisted training summaries/releases; null = not measured |
| `/api/models` | GET | Model name/dataset/size (no absolute paths) |
| `/api/config` | GET | Server configuration (both datasets) |

Training flags: `--seed`, `--partition iid|label_skew|quantity_skew`, `--alpha`, `--client-fraction`,
`--split stratified|group`, `--group-col`, `--resume`.

`train.py` writes `results/fl_state_<dataset>.npz` after every completed round
(atomic replace; gitignored). If a run dies mid-training — OOM, restart,
Ctrl-C — rerun with `--resume` to continue from the last completed round: the
client-participation RNG stream is replayed so the trajectory is identical to
an uninterrupted run (covered by `tests/test_federated.py`). The state file is
deleted after a successful full run.

### Baselines (how much does federation cost?)

```bash
cd backend
python baselines.py --dataset NF-ToN-IoT-V2 --model rf      # RandomForest
python baselines.py --dataset NF-ToN-IoT-V2 --model logreg  # Logistic regression
```

`baselines.py` trains a centralized model on the **identical raw-first split
and train-only preprocessing bundle** as `train.py`, then writes
`results/baseline_<model>_<dataset>.json` with the same metric set
(accuracy, macro-F1, balanced accuracy, per-class F1, ECE, benign FPR).
Comparing it against `training_summary_<dataset>.json` quantifies what
simulated FedAvg costs — the number to quote in a write-up.

Env: `AIPFL_MAX_FILE_MB`, `AIPFL_MAX_ROWS`, `AIPFL_MAX_COLS`, `AIPFL_MAX_BATCH_ROWS`,
`AIPFL_MAX_JOB_ROWS`, `AIPFL_MAX_CONCURRENT_JOBS`, `AIPFL_ALLOWED_ORIGINS`, `AIPFL_API_KEY`,
`AIPFL_RATE_LIMIT_PER_MIN`, `AIPFL_TRUST_PROXY`, `AIPFL_REQUIRE_MANIFEST`, `AIPFL_SEED`,
`AIPFL_PARTITION`, `AIPFL_ALPHA`, `AIPFL_CLIENT_FRACTION`, `AIPFL_MIN_CLIENTS`,
`AIPFL_CLEAR_SESSION` (default on; per-client `clear_session` keeps TF memory flat on
small-RAM hosts — set `0` to disable), `AIPFL_CSV_CHUNK_ROWS` (CSV streaming chunk size).
See `docs/DEPLOYMENT.md` and `docs/THREAT_MODEL.md`.

---

## Datasets

Raw data is **not** committed (`backend/data/raw/` is gitignored — the
datasets keep their own research-use terms). Each dataset page carries its
own citation and license; read it before redistributing anything.

- **CICIoT2023**: 6,668,822 records in the mirror we use, 34 attack labels
  merged to 10 categories, 42 model features after preprocessing. **Not
  auto-downloaded** — fetch a mirror
  such as [`himadri07/ciciot2023`](https://www.kaggle.com/datasets/himadri07/ciciot2023)
  (a verified mirror: 6,668,822 rows, all 34 original labels; other mirrors
  and the original UNB release also work) and lay the CSVs out under
  `backend/data/raw/CICIoT2023*/`.
  The loader streams multi-GB files in chunks, resolves the `label`/`Label`
  column case-insensitively, and uppercases/merges labels — so multi-file and
  single-`train.csv`/`test.csv` layouts both work.
  `train.py` aborts with an actionable error when no files match.
- **NF-ToN-IoT-V2**: 13,135,881 records, 10 classes, 41 model features after
  preprocessing. **Auto-downloaded** from KaggleHub (`dhoogla/nftoniotv2`) on
  first run and cached at `backend/data/raw/NF-ToN-IoT-V2.parquet`.

---

## Model Artifacts

Training writes the following files to `backend/models/` (all **gitignored** —
a fresh clone has no trained model until you run `train.py`, so `/predict`
and the dashboard metrics stay inactive until then):

| File | Purpose |
|------|---------|
| `CICIoT2023_Federated_Model.keras` | CICIoT2023 trained model |
| `NF_ToN_IoT_Federated_Model.keras` | NF-ToN-IoT-V2 trained model |
| `scaler_ciciot2023.pkl` | StandardScaler (CICIoT2023) |
| `scaler_nftoniotv2.pkl` | StandardScaler (NF-ToN-IoT-V2) |
| `encoder_ciciot2023.pkl` | LabelEncoder (CICIoT2023) |
| `encoder_nftoniotv2.pkl` | LabelEncoder (NF-ToN-IoT-V2) |
| `best_CICIoT2023_Federated_Model.keras` | Best checkpoint (CICIoT2023) |
| `best_NF_ToN_IoT_Federated_Model.keras` | Best checkpoint (NF-ToN-IoT-V2) |

---

## License

MIT
