#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 server/migrate.py
if [[ "${APP_ENV:-}" == "staging" && "${SEED_STAGING:-}" == "1" ]]; then
  python3 scripts/seed_dev.py || true
fi
exec python3 server/app.py
