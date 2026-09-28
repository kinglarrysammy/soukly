"""Structured request logging — no secrets."""
from __future__ import annotations

import json
import time
import uuid
from typing import Any


SENSITIVE = {"password", "token", "authorization", "cookie", "session"}


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def log_event(event: str, **fields: Any) -> None:
    safe = {k: v for k, v in fields.items() if k.lower() not in SENSITIVE}
    safe["event"] = event
    safe["ts"] = time.time()
    print(json.dumps(safe, default=str, ensure_ascii=False), flush=True)
