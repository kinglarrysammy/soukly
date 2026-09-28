"""Agent request status machine — explicit transitions only."""
from __future__ import annotations

TRANSITIONS = {
    "NEW": {"ASSIGNED", "AGENT_REQUESTED", "CANCELLED"},
    "AGENT_REQUESTED": {"ASSIGNED", "CONTACTING_OWNER", "OWNER_CONTACTED", "CANCELLED"},
    "ASSIGNED": {"CONTACTING_OWNER", "OWNER_CONTACTED", "CANCELLED"},
    "CONTACTING_OWNER": {"OWNER_CONTACTED", "AVAILABILITY_CONFIRMED", "CANCELLED"},
    "OWNER_CONTACTED": {"AVAILABILITY_CONFIRMED", "VERIFICATION_PENDING", "VERIFIED", "CANCELLED"},
    "AVAILABILITY_CONFIRMED": {"VERIFICATION_PENDING", "VERIFIED", "VIEWING_REQUESTED", "CANCELLED"},
    "VERIFICATION_PENDING": {"VERIFIED", "CANCELLED"},
    "VERIFIED": {"VIEWING_REQUESTED", "COMPLETED", "CANCELLED"},
    "VIEWING_REQUESTED": {"VIEWING_CONFIRMED", "CANCELLED"},
    "VIEWING_CONFIRMED": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
    "AI_ANALYZED": {"OPTIONS_FOUND", "SHORTLISTED", "AGENT_REQUESTED"},
    "OPTIONS_FOUND": {"SHORTLISTED", "AGENT_REQUESTED"},
    "SHORTLISTED": {"AGENT_REQUESTED", "ASSIGNED"},
}

def can_transition(current: str, new: str) -> bool:
    if current == new:
        return True
    allowed = TRANSITIONS.get(current, set())
    return new in allowed

def validate_transition(current: str, new: str) -> None:
    if not can_transition(current, new):
        raise ValueError(f"invalid_transition:{current}->{new}")
