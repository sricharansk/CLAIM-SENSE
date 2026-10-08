"""Settlement clock: the policy's settlement period runs from the last document received."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .models import Claim, ClaimDecision

DEFAULT_DAYS = 30
CLOSED = ("APPROVED", "REJECTED")


def _as_date(dt: datetime) -> date:
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).date()


def settlement_clock(claim: Claim, terms: dict | None, final: ClaimDecision | None, today: date | None = None) -> dict:
    rule = (terms or {}).get("settlement_days") or {}
    days = int(rule.get("value", DEFAULT_DAYS))
    starts = [d.uploaded_at for d in claim.documents] or [claim.created_at]
    start = _as_date(max(starts))
    due = start + timedelta(days=days)
    today = today or datetime.now(timezone.utc).date()
    if claim.status in CLOSED and final is not None:
        decided = _as_date(final.created_at)
        state = "MET" if decided <= due else "BREACHED"
        return {"start": start, "due_date": due, "days": days, "clause": rule.get("clause"),
                "days_left": None, "state": state, "decided_on": decided}
    left = (due - today).days
    state = "OVERDUE" if left < 0 else "DUE_SOON" if left <= 5 else "ON_TRACK"
    return {"start": start, "due_date": due, "days": days, "clause": rule.get("clause"),
            "days_left": left, "state": state, "decided_on": None}
