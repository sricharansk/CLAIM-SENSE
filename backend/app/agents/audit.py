"""Audit Agent: append-only audit events."""
from sqlalchemy.orm import Session

from ..models import AuditEvent


def log(db: Session, claim_id: int | None, event_type: str, actor: str, details: dict | None = None,
        correlation_id: str | None = None) -> None:
    db.add(AuditEvent(claim_id=claim_id, event_type=event_type, actor=actor, details=details or {},
                      correlation_id=correlation_id))
