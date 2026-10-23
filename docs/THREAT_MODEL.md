# Threat model — AIPFL-IDS federation

Status: simulation + documented target. Current `create_clients` partitions are
in-process array splits, not independent organisations/devices.

## In scope (implemented)

- Update validation: `weighted_fed_average` rejects empty, zero-sample,
  shape-mismatched, and non-finite updates. `validate_client_update`
  additionally bounds the *delta* norm (new − global) per client via
  `MAX_UPDATE_NORM`; over-norm deltas are skipped, not aggregated. This is
  malfunction/corruption hygiene, not Byzantine robustness — see below.
- Partial participation: per-round client sampling (`CLIENT_FRACTION`,
  `MIN_CLIENTS`); rounds with too few valid clients are skipped, counts and
  upload bytes logged in `training_summary_*.json`.
- Transport honesty: no claim of secure aggregation or differential privacy.
  Plain FedAvg lets the coordinator see individual updates.

## Not yet implemented (do not claim)

- Authenticated client identity, TLS for FL transport, secure aggregation
  (SecAgg/SecAgg+), differential privacy with clipping/noise/accounting,
  robust aggregation (trimmed mean/median/Krum), Byzantine tolerance.
- The Flask API exposes optional app-level controls (`AIPFL_API_KEY`,
  `AIPFL_RATE_LIMIT_PER_MIN`, origin allow-list) that default to **off** — they
  are shared-secret/guest-grade, not user identity or authorization. Run behind
  a reverse proxy with TLS, real authn/z, quotas, and audit logging
  (see `docs/DEPLOYMENT.md`).
- Dashboard predictions are uncalibrated model outputs (ECE reported in
  `backend/results/training_summary_<dataset>.json`), not confirmed incidents.

## Verifying the current controls

- `python -m pytest backend/tests -q` covers aggregation rejects and the
  val-only checkpoint contract.
- Train with `--partition label_skew --alpha 0.2 --client-fraction 0.5` and
  inspect `client_label_histograms`, `participating_clients`,
  `comm_bytes_upload` in `backend/results/training_summary_*.json`.
