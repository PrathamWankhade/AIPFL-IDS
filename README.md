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
│   │   ├── globals.css      # All styles (Brutalist UI, animations)
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
│   │   ├── app.py           # Flask API (dual-model, 6 endpoints)
│   │   └── requirements.txt
│   ├── src/                 # ML core
│   │   ├── model.py         # DNN architecture
│   │   ├── preprocessing.py # Feature engineering (clip_extreme, clean_infinite)
│   │   ├── federated.py     # FedAvg
│   │   ├── evaluation.py    # Metrics, confusion matrix
│   │   ├── predict.py       # Dual-model prediction service
│   │   └── utils.py         # GPU, seeds, precision
│   ├── data/raw/            # CICIoT2023 CSV (63 files) + NF-ToN-IoT-V2.parquet
│   ├── models/              # Both trained models + scalers + encoders
│   ├── uploads/             # Temporary prediction uploads
│   ├── results/             # Evaluation plots, training summary
│   ├── config.py            # Hyperparameters, dual-dataset paths
│   └── train.py             # Training pipeline (--dataset flag)
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
python train.py --dataset CICIoT2023  # Train CICIoT2023 model (10 categories)
python train.py --dataset NF-ToN-IoT-V2  # Train NF-ToN-IoT-V2 model (10 classes)
python server/app.py # -> http://localhost:5000
```

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

### CICIoT2023 Results (historical benchmark — reproduce with the released model before citing)

| Metric | Value |
|--------|-------|
| Test Accuracy | **71.35%** |
| Input Features | 39 |
| Attack Classes | 10 (merged from 34 original labels: DDOS, DOS, MIRAI, RECON, BENIGN, DICTIONARYBRUTEFORCE, DNS_SPOOFING, MITM-ARPSPOOFING, VULNERABILITYSCAN, OTHER) |
| Training Samples | 436,321 (balanced, 50K max/class) |
| Raw Records | 45,019,243 |

### NF-ToN-IoT-V2 Results (historical benchmark — reproduce with the released model before citing)

| Metric | Value |
|--------|-------|
| Test Accuracy | **79.92%** |
| Input Features | 41 |
| Attack Classes | 10 (Benign, DDoS, DoS, Injection, Ransomware, Scanning, XSS, Backdoor, Password, MITM) |
| Training Samples | 377,339 (balanced, 50K max/class) |
| Raw Records | ~13M |

---

## Features

- **Dual-Dataset Architecture**: CICIoT2023 (34 original labels mapped to 10 categories) and NF-ToN-IoT-V2 (10 classes), with separate scalers, encoders, and models
- **Robust Preprocessing**: `clip_extreme()` handles extreme byte-rate features (up to 1e+261) using percentile-based clipping
- **Streaming Batch Loading**: 200K-row batches for memory-efficient processing of 45M+ records
- **Federated Averaging (FedAvg)**: 10 clients, 10 rounds, weighted aggregation
- **Dual-Model API**: Select dataset via `?dataset=CICIoT2023` or `?dataset=NF-ToN-IoT-V2` query parameter
- **Brutalist UI**: Zero-radius, thick borders, hard shadows, monospace fonts, high contrast

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
`--split stratified|group`, `--group-col`.
Env: `AIPFL_MAX_FILE_MB`, `AIPFL_MAX_ROWS`, `AIPFL_MAX_COLS`, `AIPFL_MAX_BATCH_ROWS`,
`AIPFL_MAX_JOB_ROWS`, `AIPFL_MAX_CONCURRENT_JOBS`, `AIPFL_ALLOWED_ORIGINS`, `AIPFL_API_KEY`,
`AIPFL_RATE_LIMIT_PER_MIN`, `AIPFL_TRUST_PROXY`, `AIPFL_REQUIRE_MANIFEST`, `AIPFL_SEED`,
`AIPFL_PARTITION`, `AIPFL_ALPHA`, `AIPFL_CLIENT_FRACTION`, `AIPFL_MIN_CLIENTS`.
See `docs/DEPLOYMENT.md` and `docs/THREAT_MODEL.md`.

---

## Datasets

- **CICIoT2023**: ~45M records, 39 features, 34 attack classes. Downloaded via KaggleHub from `dhoogla/ciciot2023`.
- **NF-ToN-IoT-V2**: ~13M records, 43 features (41 after preprocessing), 10 attack classes. Pre-cached at `backend/data/raw/NF-ToN-IoT-V2.parquet`.

---

## Model Artifacts

After training, the following files are saved to `backend/models/`:

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
