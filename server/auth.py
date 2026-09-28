"""Authentication & authorization — PBKDF2 + server sessions."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from config import SESSION_DAYS
from db import connect

PBKDF2_ITERATIONS = 120_000
TOKEN_BYTES = 32
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    def __init__(self, status: int, code: str):
        self.status = status
        self.code = code
        super().__init__(code)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(TOKEN_BYTES)
    expires = (_utcnow() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sid = secrets.token_hex(8)
    conn = connect()
    conn.execute(
        "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
        (sid, user_id, token, expires),
    )
    conn.commit()
    conn.close()
    return token


def revoke_session(token: str) -> None:
    if not token:
        return
    conn = connect()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    conn = connect()
    cur = conn.execute(
        """SELECT u.id, u.name, u.phone, u.email, u.preferred_language, u.city, u.role
           FROM sessions s JOIN users u ON u.id = s.user_id
           WHERE s.token = ? AND s.expires_at > datetime('now')""",
        (token,),
    )
    user = conn.fetchone_dict(cur)
    conn.close()
    return user


def require_user(token: str | None) -> dict:
    user = user_from_token(token)
    if not user:
        raise AuthError(401, "authentication_required")
    return user


def require_roles(token: str | None, *roles: str) -> dict:
    user = require_user(token)
    if user.get("role") not in roles:
        raise AuthError(403, "forbidden")
    return user


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "role": user.get("role"),
        "city": user.get("city"),
        "preferred_language": user.get("preferred_language"),
    }


def register_user(
    *,
    name: str,
    password: str,
    role: str = "customer",
    email: str | None = None,
    phone: str | None = None,
    city: str | None = None,
    preferred_language: str = "en",
) -> dict:
    if role not in ("customer", "agent", "admin", "business"):
        raise AuthError(400, "invalid_role")
    if role in ("agent", "admin"):
        raise AuthError(403, "role_not_self_service")
    if not password or len(password) < 8:
        raise AuthError(400, "password_too_short")
    if not email and not phone:
        raise AuthError(400, "email_or_phone_required")
    if email and not EMAIL_RE.match(email):
        raise AuthError(400, "invalid_email")
    uid = secrets.token_hex(8)
    conn = connect()
    try:
        conn.execute(
            """INSERT INTO users
               (id, name, phone, email, preferred_language, city, role, password_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid, name, phone, email, preferred_language, city, role, hash_password(password)),
        )
        conn.commit()
    except Exception as e:
        conn.close()
        if "UNIQUE" in str(e).upper() or "unique" in str(e).lower():
            raise AuthError(409, "user_already_exists")
        raise
    conn.close()
    return public_user({"id": uid, "name": name, "email": email, "phone": phone, "role": role, "city": city, "preferred_language": preferred_language})


def login(identifier: str, password: str) -> tuple[dict, str]:
    identifier = (identifier or "").strip()
    password = password or ""
    if not identifier or not password:
        raise AuthError(401, "invalid_credentials")
    conn = connect()
    cur = conn.execute(
        "SELECT * FROM users WHERE email = ? OR phone = ?",
        (identifier, identifier),
    )
    user = conn.fetchone_dict(cur)
    conn.close()
    if not user or not user.get("password_hash"):
        raise AuthError(401, "invalid_credentials")
    if not verify_password(password, user["password_hash"]):
        raise AuthError(401, "invalid_credentials")
    token = create_session(user["id"])
    return public_user(user), token
