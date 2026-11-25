# Deployment — Outpost

## Topology

- Frontend: Next.js, proxies `/api/*` to Flask (see `frontend/next.config.mjs`).
  When hosts differ, set the proxy target accordingly; do not expose Flask
  directly without the controls below.
- Backend: Flask on `:5000`. `app.config["MAX_CONTENT_LENGTH"]` enforces
  `OUTPOST_MAX_FILE_MB` (default 50); `/api/predict-batch` caps at
  `OUTPOST_MAX_BATCH_ROWS` (default 5000); uploads are tempfiles deleted in
  `finally`.

## Required fronting (not in app code)

- Reverse proxy with TLS, request-size limits matching the app caps,
  authentication (API key/OIDC), per-user quotas/rate limits, access logs
  with request IDs, and separate admin functions.
- App-level (defense in depth, single-replica): set `OUTPOST_API_KEY` to
  require `X-API-Key` on `/api/predict*` and `/api/jobs*`, and
  `OUTPOST_RATE_LIMIT_PER_MIN` for a per-IP sliding-window limit. These are
  not a substitute for the proxy boundary.
- The limiter keys on the direct remote address unless `OUTPOST_TRUST_PROXY=1`
  is set behind a proxy that overwrites `X-Forwarded-For`; spoofable
  headers are otherwise ignored. Verify limits through the deployed proxy.
- CORS: `OUTPOST_ALLOWED_ORIGINS` (default localhost:3000,3001),
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
- Those artifacts are **committed**: `train.py` writes
  `results/release_<dataset>.json` (model + scaler + encoder + schema hashes)
  on every run, and a fresh clone ships the full artifact set (model, scaler,
  encoder, features, summary, manifest). After retraining, commit the updated
  models and manifests together so hashes always match the shipped weights.
- Set `OUTPOST_REQUIRE_MANIFEST=1` in production: model loading then refuses
  a missing manifest, an incomplete hash set, a dataset mismatch, or any
  tampered artifact. A colocated manifest detects mismatch, not forgery —
  sign it or store its digest separately for stronger authenticity.

## Environment

- Limits/uploads: `OUTPOST_MAX_FILE_MB`, `OUTPOST_MAX_ROWS`, `OUTPOST_MAX_COLS`,
  `OUTPOST_MAX_BATCH_ROWS`, `OUTPOST_MAX_JOB_ROWS`, `OUTPOST_MAX_CONCURRENT_JOBS`.
- Edge controls (all default off): `OUTPOST_API_KEY`, `OUTPOST_RATE_LIMIT_PER_MIN`,
  `OUTPOST_ALLOWED_ORIGINS`, `OUTPOST_TRUST_PROXY`.
- Training/run: `OUTPOST_SEED`, `OUTPOST_PARTITION`, `OUTPOST_ALPHA`,
  `OUTPOST_CLIENT_FRACTION`, `OUTPOST_MIN_CLIENTS`, `OUTPOST_REQUIRE_MANIFEST`.
