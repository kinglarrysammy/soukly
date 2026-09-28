from __future__ import annotations

import secrets
from datetime import datetime, timezone

from db import connect
from repositories.listings import listing_full


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_or_create_user_shortlist(user_id: str) -> str:
    conn = connect()
    cur = conn.execute(
        "SELECT id FROM shortlists WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = conn.fetchone_dict(cur)
    if row:
        conn.close()
        return row["id"]
    sid = "sl_" + secrets.token_hex(6)
    conn.execute(
        "INSERT INTO shortlists (id, user_id, created_at) VALUES (?, ?, ?)",
        (sid, user_id, _now()),
    )
    conn.commit()
    conn.close()
    return sid


def list_items(user_id: str) -> list[dict]:
    sid = get_or_create_user_shortlist(user_id)
    conn = connect()
    cur = conn.execute(
        "SELECT listing_id, added_at FROM shortlist_items WHERE shortlist_id = ? ORDER BY added_at DESC",
        (sid,),
    )
    rows = conn.fetchall_dicts(cur)
    out = []
    for r in rows:
        item = listing_full(conn, r["listing_id"])
        if item:
            item["addedAt"] = str(r["added_at"])
            out.append(item)
    conn.close()
    return out


def add_item(user_id: str, listing_id: str) -> list[dict]:
    sid = get_or_create_user_shortlist(user_id)
    conn = connect()
    conn.execute(
        "INSERT OR IGNORE INTO shortlist_items (shortlist_id, listing_id, added_at) VALUES (?, ?, ?)",
        (sid, listing_id, _now()),
    )
    conn.commit()
    conn.close()
    return list_items(user_id)


def remove_item(user_id: str, listing_id: str) -> list[dict]:
    sid = get_or_create_user_shortlist(user_id)
    conn = connect()
    conn.execute(
        "DELETE FROM shortlist_items WHERE shortlist_id = ? AND listing_id = ?",
        (sid, listing_id),
    )
    conn.commit()
    conn.close()
    return list_items(user_id)
