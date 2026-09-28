#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export APP_ENV="${APP_ENV:-staging}"
export SOUKLY_DB="${SOUKLY_DB:-/tmp/soukly-staging.db}"
export SOUKLY_PORT="${SOUKLY_PORT:-8787}"
export SESSION_SECRET="${SESSION_SECRET:-$(openssl rand -hex 32 2>/dev/null || echo staging-dev-secret-change-me)}"
export CORS_ORIGIN="${CORS_ORIGIN:-*}"
export COOKIE_SECURE="${COOKIE_SECURE:-false}"
cd "$ROOT"
python3 server/migrate.py
if [[ "${APP_ENV}" != "production" ]]; then
  python3 scripts/seed_dev.py || true
fi
exec python3 server/app.py
