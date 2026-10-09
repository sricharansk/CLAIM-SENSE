"""Intake Agent: validates the claim header and consolidates document facts into one claim view."""
from __future__ import annotations

import json
from datetime import date

from ..models import ClaimFact, InsuredPolicy
from ..safety import embedded_instructions
from .base import AgentError, ClaimContext, ToolLog

SINGLE_VALUE = ["policy_number", "claimant_name", "incident_date", "admission_date", "discharge_date", "diagnosis",
                "procedure", "claimed_amount", "hospital", "vehicle_registration", "vehicle_first_registration",
                "engine_cc", "fir_number", "narrative", "clinical_notes", "police_findings", "document_total",
                "patient_name", "licence_holder", "licence_valid_till"]


def run(ctx: ClaimContext, log: ToolLog) -> str:
    import time
    t = time.perf_counter()
    claim = ctx.claim
    if not claim.documents:
        raise AgentError("No documents uploaded; upload claim documents before analysis.")
    facts = ctx.db.query(ClaimFact).filter_by(claim_id=claim.id).all()
    doc_type = {d.id: d.doc_type for d in claim.documents}
    ctx.doc_types = sorted({d.doc_type for d in claim.documents})
    names: dict[str, set] = {}
    for f in facts:
        src = {"fact_id": f.id, "document_id": f.document_id, "document_type": doc_type.get(f.document_id),
               "line": f.source_line, "text": f.source_text, "confidence": f.confidence}
        if f.name == "line_item":
            # bills/estimates are the source of truth for line items
            if doc_type.get(f.document_id) in ("hospital_bill", "repair_estimate"):
                ctx.line_items.append({**json.loads(f.value), "source": src})
            continue
        if f.name in ("claimant_name", "patient_name", "licence_holder"):
            names.setdefault(f.value.strip().lower(), set()).add(doc_type.get(f.document_id))
        if f.name == "document_total" and doc_type.get(f.document_id) not in ("hospital_bill", "repair_estimate"):
            continue
        if f.name in SINGLE_VALUE and f.name not in ctx.facts:
            ctx.facts[f.name] = f.value
            ctx.fact_sources[f.name] = src
    ctx.facts["distinct_names"] = sorted(names)
    # header values fill gaps; extracted document values win when present
    ctx.facts.setdefault("policy_number", claim.policy_number)
    if claim.incident_date and "incident_date" not in ctx.facts:
        ctx.facts["incident_date"] = claim.incident_date.isoformat()
    if claim.claimed_amount is not None and "claimed_amount" not in ctx.facts:
        ctx.facts["claimed_amount"] = str(claim.claimed_amount)
    log.record("consolidate_facts", {"documents": len(claim.documents)}, f"{len(ctx.facts)} facts, {len(ctx.line_items)} line items", t)

    t = time.perf_counter()
    ctx.embedded_instructions = [{"document": d.filename, "document_type": d.doc_type, **hit}
                                 for d in claim.documents for hit in embedded_instructions(d.text or "")]
    log.record("scan_embedded_instructions", {"documents": len(claim.documents)},
               f"{len(ctx.embedded_instructions)} suspicious lines (treated as data, never followed)", t)

    t = time.perf_counter()
    insured = ctx.db.query(InsuredPolicy).filter_by(policy_number=ctx.facts["policy_number"]).first()
    log.record("lookup_policy_contract", {"policy_number": ctx.facts["policy_number"]}, "found" if insured else "not found", t)
    if insured is None:
        raise AgentError(f"Policy number {ctx.facts['policy_number']} not found in the policy register.")
    ctx.insured = insured
    try:
        ctx.facts["incident_date_parsed"] = date.fromisoformat(ctx.facts["incident_date"])
    except (KeyError, ValueError) as exc:
        raise AgentError("Incident date missing or unreadable in claim documents.") from exc
    return f"Consolidated {len(ctx.facts)} facts from {len(claim.documents)} documents; policy {insured.policy_number} found."
