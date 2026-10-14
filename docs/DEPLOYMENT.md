# Deployment — AIPFL-IDS

## Topology

- Frontend: Next.js, proxies `/api/*` to Flask (see `frontend/next.config.mjs`).
  When hosts differ, set the proxy target accordingly; do not expose Flask
  directly without the controls below.
- Backend: Flask on `:5000`. `app.config["MAX_CONTENT_LENGTH"]` enforces
  `AIPFL_MAX_FILE_MB` (default 50); `/api/predict-batch` caps at
  `AIPFL_MAX_BATCH_ROWS` (default 5000); uploads are tempfiles deleted in
  `finally`.

## Required fronting (not in app code)

- Reverse proxy with TLS, request-size limits matching the app caps,
  authentication (API key/OIDC), per-user quotas/rate limits, access logs
  with request IDs, and separate admin functions.
- CORS: `AIPFL_ALLOWED_ORIGINS` (default localhost:3000,3001),
  credentials disabled. This is not authentication.

## Health checking

- `GET /api/livez` — process liveness, no model dependency.
- `GET /api/readyz` — 200 only when model + scaler + schema + dry-run
  inference pass per dataset; 503 otherwise.
- `GET /api/metrics` — persisted `training_summary_*`/`release_*`; null
  means not measured.

## Data handling

- Uploaded files are sent to the configured server and deleted after
  prediction (success or failure). No retention beyond the request unless
  the operator adds logging/queues — document any such change.
- Release artifacts (`backend/models/`, `backend/results/release_*.json`)
  are trusted, versioned, integrity-checked (sha256 in manifest). Never load
  joblib/pickle artifacts from untrusted sources.
- Set `AIPFL_REQUIRE_MANIFEST=1` in production: model loading then refuses
  a missing manifest, an incomplete hash set, a dataset mismatch, or any
  tampered artifact. A colocated manifest detects mismatch, not forgery —
  sign it or store its digest separately for stronger authenticity.

## Environment

- `AIPFL_MAX_FILE_MB`, `AIPFL_MAX_ROWS`, `AIPFL_MAX_COLS`,
  `AIPFL_MAX_BATCH_ROWS`, `AIPFL_ALLOWED_ORIGINS`, `AIPFL_SEED`,
  `AIPFL_PARTITION`, `AIPFL_ALPHA`, `AIPFL_CLIENT_FRACTION`,
  `AIPFL_MIN_CLIENTS`.
