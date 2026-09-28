"""
Database abstraction.

- SQLite: SOUKLY_DB path (default /tmp/soukly.db) for local development
- PostgreSQL: DATABASE_URL=postgresql://... when set

Repositories must use only param placeholders via this module (qmark style
is translated for Postgres).
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQLITE = ROOT / "db" / "schema.sql"
SCHEMA_PG = ROOT / "db" / "schema_pg.sql"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SOUKLY_DB = Path(os.environ.get("SOUKLY_DB", "/tmp/soukly.db"))
APP_ENV = os.environ.get("APP_ENV", "development").lower()


def is_postgres() -> bool:
    return bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))


def _pg_connect():
    try:
        import psycopg  # type: ignore
        return psycopg.connect(DATABASE_URL)
    except ImportError:
        try:
            import psycopg2  # type: ignore
            return psycopg2.connect(DATABASE_URL)
        except ImportError as e:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg/psycopg2 is not installed. "
                "pip install 'psycopg[binary]' or use SQLite via SOUKLY_DB."
            ) from e


class Connection:
    """Thin wrapper so repositories can use execute/fetch with ? placeholders."""

    def __init__(self, raw, backend: str):
        self._raw = raw
        self.backend = backend
        if backend == "sqlite":
            self._raw.row_factory = sqlite3.Row

    def _sql(self, sql: str) -> str:
        if self.backend == "postgres":
            return sql.replace("?", "%s")
        return sql

    def execute(self, sql: str, params: tuple | list = ()):
        cur = self._raw.cursor()
        cur.execute(self._sql(sql), params)
        return cur

    def executemany(self, sql: str, seq):
        cur = self._raw.cursor()
        cur.executemany(self._sql(sql), seq)
        return cur

    def executescript(self, script: str):
        if self.backend == "sqlite":
            self._raw.executescript(script)
        else:
            cur = self._raw.cursor()
            for stmt in _split_sql(script):
                if stmt.strip():
                    cur.execute(stmt)
        return self

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()

    def fetchone_dict(self, cur) -> dict | None:
        row = cur.fetchone()
        if row is None:
            return None
        if self.backend == "sqlite":
            return {k: row[k] for k in row.keys()}
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def fetchall_dicts(self, cur) -> list[dict]:
        rows = cur.fetchall()
        if not rows:
            return []
        if self.backend == "sqlite":
            return [{k: r[k] for k in r.keys()} for r in rows]
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


def connect() -> Connection:
    if is_postgres():
        raw = _pg_connect()
        return Connection(raw, "postgres")
    SOUKLY_DB.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(str(SOUKLY_DB), check_same_thread=False)
    raw.execute("PRAGMA foreign_keys = ON")
    return Connection(raw, "sqlite")


def init_schema() -> None:
    conn = connect()
    path = SCHEMA_PG if conn.backend == "postgres" else SCHEMA_SQLITE
    if not path.exists():
        path = SCHEMA_SQLITE
    conn.executescript(path.read_text())
    conn.commit()
    conn.close()


def row_dict(row) -> dict | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return {k: row[k] for k in row.keys()}


def _split_sql(script: str) -> list[str]:
    parts = []
    buf = []
    for line in script.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if ";" in line:
            parts.append("\n".join(buf))
            buf = []
    if buf:
        parts.append("\n".join(buf))
    return parts
