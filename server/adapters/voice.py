"""Voice adapter — not live until credentials configured."""
from __future__ import annotations


def transcribe(audio_bytes: bytes, language: str | None = None) -> dict:
    return {"ok": False, "error": "voice_not_configured"}
