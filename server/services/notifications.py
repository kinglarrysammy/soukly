from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone

from db import connect


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def notify(user_id: str, *, type: str, title: str, body: str | None = None, meta: dict | None = None) -> str:
    nid = "nt_" + secrets.token_hex(6)
    conn = connect()
    conn.execute(
        """INSERT INTO notifications (id, user_id, type, title, body, read, meta, created_at)
           VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
        (nid, user_id, type, title, body, json.dumps(meta or {}), _now()),
    )
    conn.commit()
    conn.close()
    return nid


def list_for_user(user_id: str, limit: int = 50) -> list[dict]:
    conn = connect()
    cur = conn.execute(
        """SELECT id, type, title, body, read, meta, created_at
           FROM notifications WHERE user_id = ?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = conn.fetchall_dicts(cur)
    conn.close()
    out = []
    for r in rows:
        meta = r.get("meta")
        try:
            meta = json.loads(meta) if meta else {}
        except (TypeError, json.JSONDecodeError):
            meta = {}
        out.append({
            "id": r["id"], "type": r["type"], "title": r["title"], "body": r["body"],
            "read": bool(r["read"]), "meta": meta, "createdAt": str(r["created_at"]),
        })
    return out


def mark_read(user_id: str, notification_id: str) -> bool:
    conn = connect()
    cur = conn.execute(
        "UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id),
    )
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok
