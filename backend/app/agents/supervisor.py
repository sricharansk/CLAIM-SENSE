"""Supervisor / Claim Orchestrator.

Runs the specialist agents in a fixed, bounded order, persists every agent run and tool call,
and fails safely: an agent error stops the run, marks it FAILED and routes the claim to a human.
Re-running analysis is safe: it creates a new run and supersedes the previous recommendation and task.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from ..config import settings
from ..models import AgentRun, AnalysisRun, Claim, ClaimDecision
from . import adjudicator, audit, coverage, evidence, intake, policy, review, risk
from .base import AgentError, ClaimContext, ToolLog

PIPELINE = [
    ("Intake Agent", intake.run),
    ("Policy Retrieval Agent", policy.run),
    ("Coverage Agent", coverage.run),
    ("Adjudication Tool", adjudicator.run),
    ("Risk/Fraud Agent", risk.run),
    ("Evidence Agent", evidence.run),
]


def _jsonable(o):
    return json.loads(json.dumps(o, default=str))


def analyze_claim(db: Session, claim: Claim, actor: str = "system") -> AnalysisRun:
    cid = f"cs-{uuid.uuid4().hex[:12]}"
    run = AnalysisRun(claim_id=claim.id, correlation_id=cid, rules_version=settings.rules_version)
    db.add(run)
    claim.status = "ANALYZING"
    db.flush()
    audit.log(db, claim.id, "ANALYSIS_STARTED", actor, {"analysis_run_id": run.id}, cid)
    ctx = ClaimContext(db=db, claim=claim, correlation_id=cid)
    for name, fn in PIPELINE:
        log, t = ToolLog(), time.perf_counter()
        try:
            summary = fn(ctx, log)
            db.add(AgentRun(analysis_run_id=run.id, agent=name, status="SUCCEEDED", summary=summary,
                            tool_calls=_jsonable(log.calls), duration_ms=int((time.perf_counter() - t) * 1000)))
        except AgentError as exc:
            db.add(AgentRun(analysis_run_id=run.id, agent=name, status="FAILED", summary=str(exc),
                            tool_calls=_jsonable(log.calls), duration_ms=int((time.perf_counter() - t) * 1000)))
            run.status, run.error, run.finished_at = "FAILED", f"{name}: {exc}", datetime.now(timezone.utc)
            claim.status = "NEEDS_ATTENTION"
            audit.log(db, claim.id, "ANALYSIS_FAILED", "supervisor", {"agent": name, "error": str(exc)}, cid)
            db.commit()
            return run

    run.policy_version_id = ctx.version.id
    facts = {k: v for k, v in ctx.facts.items() if k != "incident_date_parsed"}
    run.result = _jsonable({
        "claim_number": claim.claim_number, "correlation_id": cid,
        "policy": {"policy_number": ctx.insured.policy_number, "holder": ctx.insured.holder_name,
                   "product_code": ctx.version.policy.product_code, "product_name": ctx.version.policy.name,
                   "version": ctx.version.version, "effective_from": ctx.version.effective_from,
                   "effective_to": ctx.version.effective_to, "sum_insured": ctx.insured.sum_insured,
                   "start_date": ctx.insured.start_date, "end_date": ctx.insured.end_date},
        "facts": facts, "fact_sources": ctx.fact_sources, "line_items": ctx.line_items,
        "coverage": ctx.coverage, "adjudication": ctx.adjudication, "risk": ctx.risk,
        "evidence": ctx.evidence, "retrieval": ctx.retrieved, "recommendation": ctx.recommendation,
    })
    run.status, run.finished_at = "SUCCEEDED", datetime.now(timezone.utc)
    rec = ctx.recommendation
    db.add(ClaimDecision(claim_id=claim.id, analysis_run_id=run.id, source="AI", decision=rec["decision"],
                         payable_amount=Decimal(rec["payable_amount"]), actor="claim-sense-supervisor",
                         notes=rec["summary"]))
    t = time.perf_counter()
    task = review.route(db, claim, rec["decision"])
    db.add(AgentRun(analysis_run_id=run.id, agent="Review/Workflow Agent", status="SUCCEEDED",
                    summary=f"Routed to {task.queue} ({task.priority} priority) for human decision.",
                    tool_calls=[{"tool": "route_to_queue", "args": {"recommendation": rec["decision"]},
                                 "result": task.queue, "ms": int((time.perf_counter() - t) * 1000)}]))
    audit.log(db, claim.id, "AI_RECOMMENDATION", "claim-sense-supervisor",
              {"decision": rec["decision"], "payable_amount": rec["payable_amount"], "risk": ctx.risk["level"],
               "coverage": ctx.coverage["status"], "policy_version": ctx.version.version,
               "rules_version": settings.rules_version, "analysis_run_id": run.id}, cid)
    db.add(AgentRun(analysis_run_id=run.id, agent="Audit Agent", status="SUCCEEDED",
                    summary="Recorded analysis and recommendation in the audit trail.", tool_calls=[]))
    db.commit()
    return run
