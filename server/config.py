"""Central configuration from environment. Never commit secrets."""
from __future__ import annotations

import os


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


APP_ENV = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*" if not IS_PRODUCTION else PUBLIC_BASE_URL)
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-only-change-me")
SESSION_DAYS = _int("SESSION_DAYS", 14)
COOKIE_SECURE = _bool("COOKIE_SECURE", IS_PRODUCTION)
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")
COOKIE_NAME = os.environ.get("COOKIE_NAME", "soukly_session")

ALLOW_LOCAL_FALLBACK = _bool("ALLOW_LOCAL_FALLBACK", not IS_PRODUCTION)

RATE_LIMIT_WINDOW = _int("RATE_LIMIT_WINDOW", 60)
RATE_LIMIT_LOGIN = _int("RATE_LIMIT_LOGIN", 10)
RATE_LIMIT_REGISTER = _int("RATE_LIMIT_REGISTER", 5)
RATE_LIMIT_SEARCH = _int("RATE_LIMIT_SEARCH", 60)
RATE_LIMIT_AGENT_REQUEST = _int("RATE_LIMIT_AGENT_REQUEST", 20)
RATE_LIMIT_LISTING_CREATE = _int("RATE_LIMIT_LISTING_CREATE", 30)

OBJECT_STORAGE_PROVIDER = os.environ.get("OBJECT_STORAGE_PROVIDER", "")
OBJECT_STORAGE_BUCKET = os.environ.get("OBJECT_STORAGE_BUCKET", "")
OBJECT_STORAGE_REGION = os.environ.get("OBJECT_STORAGE_REGION", "")
OBJECT_STORAGE_ACCESS_KEY = os.environ.get("OBJECT_STORAGE_ACCESS_KEY", "")
OBJECT_STORAGE_SECRET_KEY = os.environ.get("OBJECT_STORAGE_SECRET_KEY", "")
OBJECT_STORAGE_ENDPOINT = os.environ.get("OBJECT_STORAGE_ENDPOINT", "")
OBJECT_STORAGE_PUBLIC_BASE = os.environ.get("OBJECT_STORAGE_PUBLIC_BASE", "")
MAX_UPLOAD_BYTES = _int("MAX_UPLOAD_BYTES", 5 * 1024 * 1024)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SOUKLY_DB = os.environ.get("SOUKLY_DB", "/tmp/soukly.db")
SOUKLY_PORT = _int("PORT", _int("SOUKLY_PORT", 8787))


def validate_production() -> None:
    if APP_ENV not in ("production",):
        return
    errors = []
    if not os.environ.get("DATABASE_URL", "").startswith(("postgres://", "postgresql://")):
        errors.append("DATABASE_URL must be PostgreSQL in production")
    secret = os.environ.get("SESSION_SECRET", "")
    if not secret or secret in ("dev-only-change-me", "replace-with-long-random-string", ""):
        errors.append("SESSION_SECRET must be a strong secret in production")
    if CORS_ORIGIN == "*":
        errors.append("CORS_ORIGIN must not be * in production")
    if not COOKIE_SECURE:
        errors.append("COOKIE_SECURE must be true in production")
    if errors:
        raise SystemExit("Production configuration errors:\n- " + "\n- ".join(errors))
