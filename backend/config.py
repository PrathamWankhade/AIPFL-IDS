import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

# ── CICIoT2023 ─────────────────────────────────────────────────────
CICIOT2023_PATTERN = "raw/CICIoT2023 */*.csv"
CICIOT2023_LABEL_COL = "Label"
CICIOT2023_MAX_SAMPLES_PER_CLASS = 50000
CICIOT2023_TOTAL_RECORDS = 45019243
CICIOT2023_NUM_CLASSES = 10
CICIOT2023_NUM_FEATURES = 39
CICIOT2023_MODEL_NAME = "CICIoT2023_Federated_Model.keras"

# ── NF-ToN-IoT-V2 ──────────────────────────────────────────────────
NFTONIOTV2_FILE = "NF-ToN-IoT-V2.parquet"
NFTONIOTV2_SOURCE = "dhoogla/nftoniotv2"
NFTONIOTV2_LABEL_COL = "Attack"
NFTONIOTV2_MAX_SAMPLES_PER_CLASS = 50000
NFTONIOTV2_TOTAL_RECORDS = 13000000
NFTONIOTV2_NUM_CLASSES = 10
NFTONIOTV2_NUM_FEATURES = 39
NFTONIOTV2_MODEL_NAME = "NF_ToN_IoT_Federated_Model.keras"

# ── Both model paths ───────────────────────────────────────────────
CICIOT2023_MODEL_PATH = MODELS_DIR / CICIOT2023_MODEL_NAME
CICIOT2023_BEST_PATH = MODELS_DIR / f"best_{CICIOT2023_MODEL_NAME}"
NFTONIOTV2_MODEL_PATH = MODELS_DIR / NFTONIOTV2_MODEL_NAME
NFTONIOTV2_BEST_PATH = MODELS_DIR / f"best_{NFTONIOTV2_MODEL_NAME}"
CICIOT2023_SCALER = MODELS_DIR / "scaler_ciciot2023.pkl"
CICIOT2023_ENCODER = MODELS_DIR / "encoder_ciciot2023.pkl"
CICIOT2023_FEATURES = MODELS_DIR / "features_ciciot2023.pkl"
NFTONIOTV2_SCALER = MODELS_DIR / "scaler_nftoniotv2.pkl"
NFTONIOTV2_ENCODER = MODELS_DIR / "encoder_nftoniotv2.pkl"
NFTONIOTV2_FEATURES = MODELS_DIR / "features_nftoniotv2.pkl"

# ── Model architecture ─────────────────────────────────────────────
DENSE_UNITS = [512, 256, 128]
DROPOUT_RATES = [0.30, 0.30, 0.20]
L2_REG = 1e-4

# ── Training ───────────────────────────────────────────────────────
LEARNING_RATE = 0.001
CLIPNORM = 1.0
BATCH_SIZE = 1024
EPOCHS_PER_CLIENT = 5
GLOBAL_ROUNDS = 30
NUM_CLIENTS = 10
TEST_SPLIT = 0.20
VALIDATION_SPLIT = 0.15  # fraction of (train+val) held out as validation; test is never used for selection
MAX_UPDATE_NORM = 100.0  # reject client updates with larger L2 norm (audit P1)

EARLY_STOPPING_PATIENCE = 2
REDUCE_LR_PATIENCE = 1
REDUCE_LR_FACTOR = 0.5
MIN_LR = 1e-6

SEED = int(os.environ.get("AIPFL_SEED", "42"))
RANDOM_STATE = SEED
MIXED_PRECISION = "mixed_float16"
CLIENT_PARTITION = os.environ.get("AIPFL_PARTITION", "iid")
DIRICHLET_ALPHA = float(os.environ.get("AIPFL_ALPHA", "0.5"))
CLIENT_FRACTION = float(os.environ.get("AIPFL_CLIENT_FRACTION", "1.0"))
MIN_CLIENTS = int(os.environ.get("AIPFL_MIN_CLIENTS", "1"))

# ── Server ─────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = int(os.environ.get("AIPFL_MAX_FILE_MB", "50"))
ALLOWED_EXTENSIONS = {".csv", ".parquet"}
MAX_UPLOAD_ROWS = int(os.environ.get("AIPFL_MAX_ROWS", "100000"))
MAX_UPLOAD_COLUMNS = int(os.environ.get("AIPFL_MAX_COLS", "200"))
MAX_BATCH_ROWS = int(os.environ.get("AIPFL_MAX_BATCH_ROWS", "5000"))
MAX_JOB_ROWS = int(os.environ.get("AIPFL_MAX_JOB_ROWS", "1000000"))
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get(
    "AIPFL_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",") if o.strip()]
# Optional app-level controls (off by default; REQUIRED when exposed beyond
# localhost — the reverse proxy remains the primary boundary).
API_KEY = os.environ.get("AIPFL_API_KEY") or None
RATE_LIMIT_PER_MIN = int(os.environ.get("AIPFL_RATE_LIMIT_PER_MIN", "0"))
# Trust X-Forwarded-For only behind a proxy that overwrites it. Default off:
# spoofable headers must never select the rate-limit bucket on direct exposure.
TRUST_PROXY = os.environ.get("AIPFL_TRUST_PROXY", "0") == "1"

for d in [MODELS_DIR, UPLOAD_DIR, DATA_DIR / "raw", DATA_DIR / "processed", RESULTS_DIR]:
    os.makedirs(d, exist_ok=True)
