# AIPFL-IDS

**AI-Powered Federated Learning Intrusion Detection System**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](#)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)](#)
[![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)](#)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

Privacy-preserving cybersecurity platform using Deep Learning + Federated Learning to detect malicious IoT network traffic without sharing raw data.

---

## Architecture

```
frontend/ (Next.js :3000)        backend/ (Flask :5000)
/home  /about  /dashboard         POST /api/predict
/predict  /contact                GET  /api/status
         |                             /api/health
         |  fetch /api/*              /api/models
         +-------- proxy ----------+  /api/config
                                        |
                                    src/ — ML Pipeline
                                    TensorFlow DNN 512→256→128→64→10
                                    FedAvg, StandardScaler, LabelEncoder
```

---

## Project Structure

```
AIPFL-IDS/
├── frontend/                # Next.js (React, TypeScript)
│   ├── app/                 # App Router pages
│   │   ├── layout.tsx       # Root layout (Navbar, Footer, Theme)
│   │   ├── page.tsx         # Home page
│   │   ├── globals.css      # All styles (Brutalist UI, animations)
│   │   ├── about/           # About page
│   │   ├── dashboard/       # Live metrics dashboard
│   │   ├── predict/         # File upload & ML prediction
│   │   └── contact/         # Contact form
│   ├── components/          # Reusable React components
│   ├── lib/api.ts           # API client (fetch wrapper)
│   ├── package.json
│   ├── next.config.mjs      # API proxy /api/* -> :5000
│   └── tsconfig.json
│
├── backend/                 # Python Flask + ML
│   ├── server/
│   │   ├── app.py           # Flask API (6 endpoints)
│   │   └── requirements.txt
│   ├── src/                 # ML core
│   │   ├── model.py         # DNN architecture
│   │   ├── preprocessing.py # Feature engineering
│   │   ├── federated.py     # FedAvg
│   │   ├── evaluation.py    # Metrics, confusion matrix
│   │   ├── predict.py       # Prediction service
│   │   └── utils.py         # GPU, seeds, precision
│   ├── data/raw/            # NF-ToN-IoT-V2.parquet (13M records)
│   ├── models/              # Trained model artifacts
│   ├── uploads/             # Temporary prediction uploads
│   ├── results/             # Evaluation plots, training summary
│   ├── config.py            # Hyperparameters, paths
│   └── train.py             # Training pipeline
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
python train.py      # Train the model (may take hours on CPU)
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
python train.py
```

Loads NF-ToN-IoT-V2 from `data/raw/`, balances per class (50K max), splits across 10 federated clients, trains via FedAvg, saves model + artifacts to `models/`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `GLOBAL_ROUNDS` | 10 | Federated communication rounds |
| `NUM_CLIENTS` | 10 | Simulated clients |
| `EPOCHS_PER_CLIENT` | 3 | Local epochs per round |
| `BATCH_SIZE` | 1024 | Training batch size |
| `LEARNING_RATE` | 0.0005 | Adam learning rate |
| `DENSE_UNITS` | [512,256,128,64] | Hidden layers |
| `MAX_SAMPLES_PER_CLASS` | 50000 | Class balance cap |

### Results
- **Test Accuracy:** 79.85%
- **Input Features:** 39
- **Attack Classes:** 10 (Benign, DDoS, DoS, Injection, Ransomware, Scanning, XSS, backdoor, password, mitm)
- **Training Samples:** 377,339 (balanced, 50K max/class)

---

## API Reference

All endpoints at `/api/*` (proxied to Flask). Response format: `{success: bool, data?: ..., error?: string}`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict` | POST | Upload CSV/Parquet file -> predictions |
| `/api/predict-batch` | POST | JSON `{features: [...]}` -> predictions |
| `/api/status` | GET | Server + model status |
| `/api/health` | GET | Health check with uptime |
| `/api/models` | GET | List trained model files |
| `/api/config` | GET | Server configuration |

---

## Dataset

**NF-ToN-IoT-V2**: ~13M records, 43 features, 10 attack classes (Benign, DDoS, DoS, Injection, Ransomware, Scanning, XSS, backdoor, password, mitm). Pre-cached at `backend/data/raw/NF-ToN-IoT-V2.parquet`.

---

## License

MIT
