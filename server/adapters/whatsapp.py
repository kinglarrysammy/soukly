"""WhatsApp adapter — not live until credentials configured."""
from __future__ import annotations


def send_message(to: str, body: str) -> dict:
    return {"ok": False, "error": "whatsapp_not_configured"}
