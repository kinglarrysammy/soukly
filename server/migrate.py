#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))
from db import connect, is_postgres, SCHEMA_SQLITE, SCHEMA_PG

MIGRATIONS = ROOT / "db" / "migrations"

def ensure_meta(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )"""
    )
    conn.commit()

def applied(conn):
    try:
        cur = conn.execute("SELECT id FROM schema_migrations")
        return {r["id"] for r in conn.fetchall_dicts(cur)}
    except Exception:
        return set()

def apply_all():
    conn = connect()
    ensure_meta(conn)
    done = applied(conn)
    if "0000_base" not in done:
        schema = SCHEMA_PG if conn.backend == "postgres" else SCHEMA_SQLITE
        print(f"Applying base schema {schema.name}")
        conn.executescript(schema.read_text())
        conn.execute("INSERT OR IGNORE INTO schema_migrations (id) VALUES (?)", ("0000_base",))
        conn.commit()
        done.add("0000_base")
    for path in sorted(MIGRATIONS.glob("*.sql")):
        mid = path.stem
        if mid.startswith("0001_init"):
            continue
        if mid in done:
            print(f"skip {mid}")
            continue
        print(f"apply {mid}")
        sql = path.read_text()
        if conn.backend == "sqlite":
            sql = sql.replace("TIMESTAMPTZ", "TEXT").replace("BOOLEAN", "INTEGER")
            sql = sql.replace("DOUBLE PRECISION", "REAL")
        try:
            conn.executescript(sql)
        except Exception as e:
            for stmt in sql.split(";"):
                s = stmt.strip()
                if not s or s.startswith("--"):
                    continue
                try:
                    conn.execute(s)
                except Exception as e2:
                    if "already exists" not in str(e2).lower():
                        print(f"  warn: {e2}")
        conn.execute("INSERT OR IGNORE INTO schema_migrations (id) VALUES (?)", (mid,))
        conn.commit()
    conn.close()
    print("Migrations complete")

if __name__ == "__main__":
    apply_all()
