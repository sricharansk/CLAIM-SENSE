"""Review/Workflow Agent: routes the AI recommendation to the right human queue and applies reviewer actions."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import Claim, ClaimDecision, WorkflowTask
from . import audit

QUEUES = {"INVESTIGATE": ("SIU_INVESTIGATION", "HIGH"), "REQUEST_INFO": ("PENDING_INFORMATION", "MEDIUM"),
          "RECOMMEND_REJECT": ("ADJUSTER_REVIEW", "MEDIUM"), "PARTIAL_APPROVAL": ("ADJUSTER_REVIEW", "NORMAL"),
          "APPROVE": ("ADJUSTER_REVIEW", "NORMAL")}

ACTIONS = {"APPROVE": "APPROVED", "REJECT": "REJECTED", "REQUEST_INFO": "INFO_REQUESTED",
           "INVESTIGATE": "UNDER_INVESTIGATION", "ESCALATE": "ESCALATED"}


def route(db: Session, claim: Claim, recommendation: str) -> WorkflowTask:
    now = datetime.now(timezone.utc)
    for t in db.query(WorkflowTask).filter_by(claim_id=claim.id, status="OPEN").all():
        t.status, t.closed_at = "SUPERSEDED", now
    queue, priority = QUEUES[recommendation]
    task = WorkflowTask(claim_id=claim.id, queue=queue, priority=priority)
    db.add(task)
    claim.status = "PENDING_REVIEW"
    return task


def apply_review(db: Session, claim: Claim, action: str, reviewer: str, notes: str,
                 payable_override: Decimal | None, ai_payable: Decimal | None) -> ClaimDecision:
    if action not in ACTIONS:
        raise ValueError(f"Unknown action {action}")
    payable = None
    if action == "APPROVE":
        payable = payable_override if payable_override is not None else ai_payable
    decision = ClaimDecision(claim_id=claim.id, source="HUMAN", decision=action, payable_amount=payable,
                             actor=reviewer, notes=notes)
    db.add(decision)
    claim.status = ACTIONS[action]
    now = datetime.now(timezone.utc)
    for t in db.query(WorkflowTask).filter_by(claim_id=claim.id, status="OPEN").all():
        if action == "ESCALATE":
            t.queue, t.priority, t.assignee = "SUPERVISOR_REVIEW", "HIGH", None
        elif action in ("REQUEST_INFO", "INVESTIGATE"):
            t.queue = "PENDING_INFORMATION" if action == "REQUEST_INFO" else "SIU_INVESTIGATION"
            t.assignee = reviewer
        else:
            t.status, t.closed_at, t.assignee = "CLOSED", now, reviewer
    overridden = payable_override is not None and ai_payable is not None and payable_override != ai_payable
    audit.log(db, claim.id, "HUMAN_DECISION", reviewer,
              {"action": action, "payable_amount": str(payable) if payable is not None else None,
               "ai_payable_amount": str(ai_payable) if ai_payable is not None else None,
               "override": overridden, "final": action in ("APPROVE", "REJECT"), "notes": notes})
    return decision
