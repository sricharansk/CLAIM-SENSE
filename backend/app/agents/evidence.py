"""Evidence Agent: assembles the evidence package and the recommendation (decision support only)."""
from __future__ import annotations

import time
from decimal import Decimal

from .base import ClaimContext, ToolLog

LABELS = {
    "APPROVE": "Approve in full",
    "PARTIAL_APPROVAL": "Approve the payable amount after policy deductions",
    "RECOMMEND_REJECT": "Reject, citing the policy clause",
    "REQUEST_INFO": "Request missing information",
    "INVESTIGATE": "Refer for investigation before payment",
}


def recommend(coverage: dict, risk: dict, adjudication: dict) -> tuple[str, list[str]]:
    reasons = []
    if coverage["status"] == "NOT_COVERED":
        fail = next(f for f in coverage["findings"] if f["outcome"] == "FAIL")
        return "RECOMMEND_REJECT", [fail["message"]]
    if coverage["missing_documents"] or coverage["status"] == "UNCERTAIN":
        reasons = [f["message"] for f in coverage["findings"] if f["outcome"] == "MISSING"]
        return "REQUEST_INFO", reasons
    if risk["level"] == "HIGH":
        return "INVESTIGATE", [s["message"] for s in risk["signals"]]
    payable, claimed = Decimal(adjudication["payable_amount"]), Decimal(adjudication["claimed_amount"])
    if payable < claimed:
        return "PARTIAL_APPROVAL", [f"Policy deductions reduce {claimed} to {payable}."]
    return "APPROVE", ["All checks passed and the full claimed amount is payable."]


def run(ctx: ClaimContext, log: ToolLog) -> str:
    t = time.perf_counter()
    ev: list[dict] = []
    seen = set()
    for f in ctx.coverage["findings"]:
        c = f.get("citation")
        if c:
            ev.append({"kind": "policy_clause", "used_for": f["code"], "finding": f["message"], **c})
            seen.add(c["clause_id"])
    for step in ctx.adjudication["waterfall"]:
        ref = step.get("clause_ref")
        if ref:
            from ..rag import service as rag
            c = rag.clause_by_ref(ctx.db, ctx.version.id, ref)
            if c and c.id not in seen:
                ev.append({"kind": "policy_clause", "used_for": step["rule_id"], "finding": step["label"], **rag.citation(c)})
                seen.add(c.id)
    for h in ctx.retrieved:
        if h["clause_id"] not in seen and h["score"] >= 0.15:
            ev.append({"kind": "retrieved_clause", "used_for": "RAG_CONTEXT", "finding": "Retrieved as relevant to the diagnosis/loss", **h})
            seen.add(h["clause_id"])
    for name, src in ctx.fact_sources.items():
        if name in ("diagnosis", "procedure", "incident_date", "claimed_amount", "police_findings", "vehicle_first_registration"):
            ev.append({"kind": "claim_fact", "used_for": name, "finding": f"{name} = {ctx.facts[name]}", **src})
    ctx.evidence = ev
    decision, reasons = recommend(ctx.coverage, ctx.risk, ctx.adjudication)
    a = ctx.adjudication
    summary = (f"{LABELS[decision]}. Coverage: {ctx.coverage['status']}. Billed {a['gross_billed']}, payable "
               f"{a['payable_amount']} under {ctx.version.policy.product_code} v{ctx.version.version}. "
               f"Risk {ctx.risk['level']} ({ctx.risk['score']}). A human reviewer makes the final decision.")
    ctx.recommendation = {"decision": decision, "label": LABELS[decision], "reasons": reasons, "summary": summary,
                          "payable_amount": a["payable_amount"], "requires_human_review": True}
    log.record("build_evidence_package", {}, f"{len(ev)} evidence items; {decision}", t)
    return f"{len(ev)} evidence items; recommendation {decision}."
