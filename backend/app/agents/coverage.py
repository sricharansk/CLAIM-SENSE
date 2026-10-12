"""Coverage / Exclusion Agent: policy-in-force, waiting periods, exclusions and required documents.

Checks are deterministic over extracted facts and the structured terms; each finding cites the clause.
"""
from __future__ import annotations

import time
from datetime import date

from ..rag import service as rag
from .base import ClaimContext, ToolLog

ACCIDENT_WORDS = ("accident", "accidental", "fall", "injury", "collision", "fracture")
TEXT_FACTS = ("diagnosis", "procedure", "narrative", "clinical_notes", "police_findings", "survey_findings", "report_remarks")


def _date(value) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _cite(ctx: ClaimContext, ref: str | None) -> dict | None:
    if not ref:
        return None
    c = rag.clause_by_ref(ctx.db, ctx.version.id, ref)
    return rag.citation(c) if c else None


def run(ctx: ClaimContext, log: ToolLog) -> str:
    t = time.perf_counter()
    terms, f, ins = ctx.version.terms, ctx.facts, ctx.insured
    incident = f["incident_date_parsed"]
    text = " ".join(str(f.get(k, "")) for k in TEXT_FACTS).lower()
    accident = any(w in text for w in ACCIDENT_WORDS)
    findings: list[dict] = []
    status = "COVERED"

    def add(code, outcome, message, ref=None):
        findings.append({"code": code, "outcome": outcome, "message": message, "citation": _cite(ctx, ref)})

    if not (ins.start_date <= incident <= ins.end_date):
        status = "NOT_COVERED"
        add("POLICY_NOT_IN_FORCE", "FAIL", f"Incident {incident} is outside the policy period {ins.start_date} to {ins.end_date}.")
    else:
        add("POLICY_IN_FORCE", "PASS", f"Incident {incident} is within the policy period {ins.start_date} to {ins.end_date}.",
            terms.get("coverage_clause"))

    trip = terms.get("trip_period_clause")
    if status == "COVERED" and trip:
        dep, ret = _date(f.get("departure_date")), _date(f.get("return_date"))
        if dep and ret and not (dep <= incident <= ret):
            status = "NOT_COVERED"
            add("OUTSIDE_TRIP", "FAIL", f"Incident {incident} is outside the insured trip {dep} to {ret}.", trip)
        elif dep and ret:
            add("WITHIN_TRIP", "PASS", f"Incident {incident} is within the insured trip {dep} to {ret}.", trip)

    days = (incident - ins.start_date).days
    wp = terms.get("waiting_periods", {})
    if status == "COVERED" and "initial_days" in wp:
        w = wp["initial_days"]
        if days < w["value"] and not (accident and w.get("accident_exempt")):
            status = "NOT_COVERED"
            add("INITIAL_WAITING_PERIOD", "FAIL", f"Illness {days} days after commencement, inside the {w['value']}-day initial waiting period.", w["clause"])
        else:
            add("INITIAL_WAITING_PERIOD", "PASS", f"{days} days since commencement" + (" (accident)" if accident else "") + ".", w["clause"])
    if status == "COVERED" and "specified_months" in wp:
        w = wp["specified_months"]
        hit = next((c for c in w["conditions"] if c in text), None)
        months = days // 30
        if hit and months < w["value"] and not (accident and w.get("accident_exempt")):
            status = "NOT_COVERED"
            add("SPECIFIED_DISEASE_WAITING", "FAIL",
                f"'{hit}' is a specified condition with a {w['value']}-month waiting period; cover has run about {months} months.", w["clause"])
        elif hit:
            add("SPECIFIED_DISEASE_WAITING", "PASS", f"'{hit}' waiting period of {w['value']} months has elapsed.", w["clause"])
    ped = wp.get("ped_months")
    if status == "COVERED" and ped and ped.get("keywords"):
        hit = next((k for k in ped["keywords"] if k in text), None)
        months = days // 30
        if hit and months < ped["value"]:
            status = "NOT_COVERED"
            add("PED_WAITING_PERIOD", "FAIL",
                f"Documents mention '{hit}'; a pre-existing disease has a {ped['value']}-month waiting period and cover has run about {months} months.",
                ped["clause"])
        elif hit:
            add("PED_WAITING_PERIOD", "PASS", f"Pre-existing disease waiting period of {ped['value']} months has elapsed.", ped["clause"])
    if status == "COVERED":
        for ex in terms.get("exclusions", []):
            kw = next((k for k in ex["keywords"] if k in text), None)
            if kw:
                status = "NOT_COVERED"
                add(ex["code"], "FAIL", f"Claim documents mention '{kw}', which falls under an exclusion.", ex["clause"])
                break
        else:
            add("EXCLUSIONS", "PASS", "No exclusion keywords found in diagnosis, procedure or narrative.")

    req = terms.get("required_documents", {})
    needed = list(req.get("documents", []))
    for cond in terms.get("conditional_documents", []):
        if cond["document"] not in needed and any(k in text for k in cond["keywords"]):
            needed.append(cond["document"])
    missing = [d for d in needed if d not in ctx.doc_types]
    if missing:
        add("REQUIRED_DOCUMENTS", "MISSING", f"Missing required documents: {', '.join(missing)}.", req.get("clause"))
    else:
        add("REQUIRED_DOCUMENTS", "PASS", "All required documents received.", req.get("clause"))
    if not ctx.line_items:
        status = "UNCERTAIN" if status == "COVERED" else status
        add("ITEMISED_BILL", "MISSING", "No itemised charges were found, so the amount cannot be assessed.")

    ctx.coverage = {"status": status, "accident": accident, "days_since_commencement": days,
                    "missing_documents": missing, "findings": findings}
    log.record("evaluate_coverage_rules", {"version": ctx.version.version}, status, t)
    return f"Coverage {status}; {sum(1 for x in findings if x['outcome'] == 'FAIL')} failing checks; missing docs: {missing or 'none'}."
