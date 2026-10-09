"""Risk / Fraud Agent: transparent weighted signals. A risk score never decides a claim on its own."""
from __future__ import annotations

import time
from decimal import Decimal

from ..config import settings
from ..models import Claim
from .base import ClaimContext, ToolLog

WEIGHTS = {"HIGH_AMOUNT_RATIO": 30, "ELEVATED_AMOUNT_RATIO": 15, "EARLY_CLAIM": 20, "FREQUENT_CLAIMS": 20,
           "POSSIBLE_DUPLICATE": 50, "AMOUNT_MISMATCH": 25, "NAME_MISMATCH": 20, "MISSING_DOCUMENTS": 10,
           "EMBEDDED_INSTRUCTIONS": 50}


def score_features(f: dict) -> tuple[int, list[dict]]:
    """Pure scoring function, shared by the live agent and the synthetic-portfolio evaluation."""
    signals = []

    def sig(code, message):
        signals.append({"code": code, "weight": WEIGHTS[code], "message": message})

    ratio = f.get("amount_ratio", 0)
    if ratio >= 0.8:
        sig("HIGH_AMOUNT_RATIO", f"Claimed amount is {ratio:.0%} of the sum insured.")
    elif ratio >= 0.5:
        sig("ELEVATED_AMOUNT_RATIO", f"Claimed amount is {ratio:.0%} of the sum insured.")
    if f.get("days_since_start") is not None and f["days_since_start"] < 90:
        sig("EARLY_CLAIM", f"Loss occurred {f['days_since_start']} days after policy start.")
    if f.get("prior_claims", 0) >= 2:
        sig("FREQUENT_CLAIMS", f"{f['prior_claims']} other claims on this policy in the last 12 months.")
    if f.get("duplicate_of"):
        sig("POSSIBLE_DUPLICATE", f"Same policy, incident date and amount as {f['duplicate_of']}.")
    if f.get("amount_gap", 0) > 0.02:
        sig("AMOUNT_MISMATCH", f"Claim form amount differs from the itemised document total by {f['amount_gap']:.0%}.")
    if f.get("name_mismatch"):
        sig("NAME_MISMATCH", "Names differ across claim documents.")
    if f.get("missing_documents"):
        sig("MISSING_DOCUMENTS", f"Missing documents: {', '.join(f['missing_documents'])}.")
    if f.get("embedded_instructions"):
        sig("EMBEDDED_INSTRUCTIONS", "Document text addressed to an AI system, ignored and flagged for the reviewer: "
            + "; ".join(f"{h['document']} line {h['line']}: \"{h['text'][:90]}\"" for h in f["embedded_instructions"][:3]))
    return min(100, sum(s["weight"] for s in signals)), signals


def level(score: int) -> str:
    return "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"


def run(ctx: ClaimContext, log: ToolLog) -> str:
    t = time.perf_counter()
    claimed = Decimal(ctx.adjudication["claimed_amount"])
    gross = Decimal(ctx.adjudication["gross_billed"])
    incident = ctx.facts["incident_date_parsed"]
    others = ctx.db.query(Claim).filter(Claim.policy_number == ctx.insured.policy_number, Claim.id != ctx.claim.id).all()
    prior = [c for c in others if c.incident_date and 0 <= (incident - c.incident_date).days <= 365]
    dup = next((c for c in others if c.incident_date == incident and c.claimed_amount
                and abs(Decimal(c.claimed_amount) - claimed) <= claimed * Decimal("0.05")
                and c.id < ctx.claim.id), None)
    features = {
        "amount_ratio": float(claimed / Decimal(ctx.insured.sum_insured)) if ctx.insured.sum_insured else 0,
        "days_since_start": ctx.coverage["days_since_commencement"],
        "prior_claims": len(prior),
        "duplicate_of": dup.claim_number if dup else None,
        "amount_gap": float(abs(claimed - gross) / gross) if gross else 0,
        "name_mismatch": len(ctx.facts.get("distinct_names", [])) > 1,
        "missing_documents": ctx.coverage["missing_documents"],
        "embedded_instructions": ctx.embedded_instructions,
    }
    score, signals = score_features(features)
    ctx.risk = {"score": score, "level": level(score), "signals": signals, "features": features,
                "rules_version": settings.risk_version}
    log.record("risk_rules", {"policy_number": ctx.insured.policy_number}, f"{level(score)} ({score})", t)
    return f"Risk {level(score)} (score {score}) from {len(signals)} signals."
