"""Decision letters generated from recorded data only (no LLM): amounts come from the rules engine,
reasons and clause text from the cited policy wording."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from .models import AnalysisRun, Claim, ClaimDecision, InsuredPolicy

KIND = {
    "APPROVE": "SETTLEMENT", "PARTIAL_APPROVAL": "SETTLEMENT", "REJECT": "REPUDIATION", "RECOMMEND_REJECT": "REPUDIATION",
    "REQUEST_INFO": "DOCUMENT_REQUEST", "INVESTIGATE": "UNDER_REVIEW", "ESCALATE": "UNDER_REVIEW",
}


def _inr(x) -> str:
    v = Decimal(str(x)).quantize(Decimal("0.01"))
    whole, frac = f"{v:.2f}".split(".")
    neg = whole.startswith("-")
    whole = whole.lstrip("-")
    # Indian digit grouping: 12,34,567
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    out = ",".join(groups + [tail]) if groups else tail
    return f"{'-' if neg else ''}INR {out}.{frac}"


def build_letter(db: Session, claim: Claim) -> dict | None:
    run = db.query(AnalysisRun).filter_by(claim_id=claim.id, status="SUCCEEDED").order_by(AnalysisRun.id.desc()).first()
    if run is None or not run.result:
        return None
    r = run.result
    human = db.query(ClaimDecision).filter_by(claim_id=claim.id, source="HUMAN").order_by(ClaimDecision.id.desc()).first()
    decision = human.decision if human else r["recommendation"]["decision"]
    final = human is not None and claim.status in ("APPROVED", "REJECTED", "INFO_REQUESTED", "UNDER_INVESTIGATION", "ESCALATED")
    kind = KIND[decision]
    insured = db.query(InsuredPolicy).filter_by(policy_number=claim.policy_number).first()
    pol = r["policy"]
    ref = f"{pol['product_code']} v{pol['version']}"
    paras: list[str] = []
    refs: list[dict] = []

    def cite(c: dict | None):
        if c:
            refs.append({"clause_ref": c["clause_ref"], "title": c["title"], "page": c["page"], "text": c["text"],
                         "policy": f"{c['product_code']} v{c['version']}"})

    if kind == "SETTLEMENT":
        payable = human.payable_amount if human and human.payable_amount is not None else Decimal(r["adjudication"]["payable_amount"])
        subject = f"Settlement of claim {claim.claim_number}"
        paras.append(f"We have assessed your claim under policy {claim.policy_number} ({pol['product_name']}, wording {ref}) "
                     f"for the incident on {r['facts'].get('incident_date')}. The amount payable is {_inr(payable)} "
                     f"against {_inr(r['adjudication']['gross_billed'])} billed.")
        lines = [s for s in r["adjudication"]["waterfall"] if Decimal(s["adjustment"]) < 0]
        if lines:
            paras.append("The following deductions apply under your policy:")
            for s in lines:
                paras.append(f"• {s['label']}: {_inr(-Decimal(s['adjustment']))}" + (f" (clause {s['clause_ref']})" if s["clause_ref"] else ""))
        if human and human.payable_amount is not None and human.payable_amount != Decimal(r["adjudication"]["payable_amount"]):
            paras.append("The reviewing officer adjusted the assessed amount after examining the documents.")
    elif kind == "REPUDIATION":
        fail = next((f for f in r["coverage"]["findings"] if f["outcome"] == "FAIL"), None)
        subject = f"Decision on claim {claim.claim_number}"
        reason = fail["message"] if fail else (human.notes if human else "The claim is not admissible under the policy.")
        paras.append(f"We have carefully reviewed your claim under policy {claim.policy_number} ({pol['product_name']}, wording {ref}). "
                     "We regret that we are unable to admit it.")
        paras.append(f"Reason: {reason}")
        if fail and fail.get("citation"):
            c = fail["citation"]
            paras.append(f"This decision relies on clause {c['clause_ref']} “{c['title']}” (page {c['page']}) of the policy wording, "
                         f"which states: “{c['text']}”")
            cite(c)
        paras.append("If you disagree with this decision you may ask for a review by replying with any further information, "
                     "or approach the insurer's grievance redressal officer.")
    elif kind == "DOCUMENT_REQUEST":
        missing = r["coverage"]["missing_documents"]
        subject = f"Documents needed for claim {claim.claim_number}"
        names = ", ".join(m.replace("_", " ") for m in missing) or "the documents listed by the claims officer"
        paras.append(f"Thank you for your claim under policy {claim.policy_number}. To complete our assessment we need: {names}.")
        req = next((f for f in r["coverage"]["findings"] if f["code"] == "REQUIRED_DOCUMENTS"), None)
        if req and req.get("citation"):
            cite(req["citation"])
            paras.append(f"Clause {req['citation']['clause_ref']} of your policy lists the documents a claim must include.")
        paras.append("The settlement period starts again from the date we receive the last necessary document.")
    else:
        subject = f"Your claim {claim.claim_number} is under review"
        paras.append(f"Thank you for your claim under policy {claim.policy_number}. It needs further review by a senior claims "
                     "officer before a decision is made. We will contact you if we need anything else.")
    if human and human.notes and kind != "REPUDIATION":
        paras.append(f"Officer's note: {human.notes}")
    return {
        "claim_number": claim.claim_number, "kind": kind, "status": "FINAL" if final else "DRAFT",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "to": {"name": claim.claimant_name, "policy_number": claim.policy_number,
               "holder": insured.holder_name if insured else claim.claimant_name},
        "from": "Claims Department, Synthetic Assurance Co. Ltd. (fictional)",
        "subject": subject, "paragraphs": paras, "references": refs,
        "signed_by": human.actor if human else None, "based_on": "human decision" if human else "AI recommendation (draft)",
    }
