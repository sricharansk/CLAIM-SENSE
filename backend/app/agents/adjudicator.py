"""Adjudication step: calls the deterministic rules engine as a tool. No LLM involvement."""
from __future__ import annotations

import time
from datetime import date
from decimal import Decimal

from ..adjudication import rules
from ..models import Claim, ClaimDecision
from .base import ClaimContext, ToolLog


def _available_sum_insured(ctx: ClaimContext) -> Decimal:
    other_ids = [c.id for c in ctx.db.query(Claim).filter(Claim.policy_number == ctx.insured.policy_number,
                                                          Claim.id != ctx.claim.id).all()]
    paid = Decimal("0")
    if other_ids:
        for d in ctx.db.query(ClaimDecision).filter(ClaimDecision.claim_id.in_(other_ids), ClaimDecision.source == "HUMAN",
                                                    ClaimDecision.decision == "APPROVE").all():
            paid += d.payable_amount or 0
    return Decimal(ctx.insured.sum_insured) - paid


def run(ctx: ClaimContext, log: ToolLog) -> str:
    t = time.perf_counter()
    items = [rules.LineItem(i["description"], rules.money(i["amount"]), i["category"]) for i in ctx.line_items]
    claimed = rules.money(ctx.facts.get("claimed_amount") or sum((i.amount for i in items), Decimal(0)))
    terms = ctx.version.terms
    cov = ctx.coverage
    if cov["status"] == "NOT_COVERED":
        fail = next(x for x in cov["findings"] if x["outcome"] == "FAIL")
        result = rules.not_admissible(items, claimed, (fail.get("citation") or {}).get("clause_ref"), fail["message"])
        args = {"mode": "not_admissible"}
    elif terms["line_of_business"] == "health":
        avail = _available_sum_insured(ctx)
        result = rules.adjudicate_health(items, claimed, terms, avail)
        args = {"mode": "health", "sum_insured_available": str(avail)}
    else:
        first_reg = ctx.facts.get("vehicle_first_registration")
        age = rules.months_between(date.fromisoformat(first_reg), ctx.facts["incident_date_parsed"]) if first_reg else 999
        cc = int(ctx.facts["engine_cc"]) if str(ctx.facts.get("engine_cc", "")).isdigit() else None
        result = rules.adjudicate_motor(items, claimed, terms, Decimal(ctx.insured.sum_insured), age, cc)
        args = {"mode": "motor", "vehicle_age_months": age, "engine_cc": cc, "idv": str(ctx.insured.sum_insured)}
    ctx.adjudication = result.as_dict()
    log.record("adjudication_rules_engine", args, f"payable {result.payable}", t)
    return f"Gross {result.gross_billed}, payable {result.payable} ({len(result.steps)} waterfall steps, {result.rules_version})."
