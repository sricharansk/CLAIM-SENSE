"""Application services shared by the API and the seeder: policy ingestion and document intake."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from .agents import audit
from .agents import document as docai
from .config import settings
from .models import Claim, ClaimDocument, ClaimFact, Policy, PolicyClause, PolicyVersion
from .rag.parser import parse_policy_markdown


class ValidationProblem(ValueError):
    pass


REQUIRED_TERMS = ("product_code", "product_name", "line_of_business", "version", "effective_from", "effective_to",
                  "deductible", "required_documents")


def ingest_policy(db: Session, markdown: str, terms: dict, source_file: str, actor: str = "system") -> PolicyVersion:
    missing = [k for k in REQUIRED_TERMS if k not in terms]
    if missing:
        raise ValidationProblem(f"Policy terms missing fields: {', '.join(missing)}")
    chunks = parse_policy_markdown(markdown)
    if not chunks:
        raise ValidationProblem("No clauses found. Use '## N. Section' and '### N.M Clause' headings.")
    refs = {c.clause_ref for c in chunks}
    cited = _clause_refs(terms)
    if unknown := sorted(cited - refs):
        raise ValidationProblem(f"Terms cite clauses that are not in the wording: {', '.join(unknown)}")
    policy = db.query(Policy).filter_by(product_code=terms["product_code"]).first()
    if policy is None:
        policy = Policy(product_code=terms["product_code"], name=terms["product_name"],
                        line_of_business=terms["line_of_business"], insurer=terms.get("insurer", ""))
        db.add(policy)
        db.flush()
    existing = db.query(PolicyVersion).filter_by(policy_id=policy.id, version=terms["version"]).first()
    if existing:
        raise ValidationProblem(f"{terms['product_code']} version {terms['version']} already exists.")
    v = PolicyVersion(policy_id=policy.id, version=terms["version"],
                      effective_from=date.fromisoformat(terms["effective_from"]),
                      effective_to=date.fromisoformat(terms["effective_to"]), source_file=source_file, terms=terms)
    db.add(v)
    db.flush()
    for c in chunks:
        db.add(PolicyClause(version_id=v.id, clause_ref=c.clause_ref, title=c.title, section=c.section, page=c.page, text=c.text))
    audit.log(db, None, "POLICY_INGESTED", actor, {"product_code": policy.product_code, "version": v.version,
                                                   "clauses": len(chunks), "source_file": source_file})
    db.flush()
    return v


def _clause_refs(obj) -> set[str]:
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "clause" and isinstance(v, str):
                out.add(v)
            elif k in ("coverage_clause", "max_liability_clause") and isinstance(v, str):
                out.add(v)
            elif k == "non_payable_categories" and isinstance(v, dict):
                out |= set(v.values())
            else:
                out |= _clause_refs(v)
    elif isinstance(obj, list):
        for x in obj:
            out |= _clause_refs(x)
    return out


ALLOWED_EXT = (".pdf", ".txt", ".md")


def add_document(db: Session, claim: Claim, filename: str, data: bytes, actor: str = "system") -> ClaimDocument:
    safe = Path(filename).name
    if not safe.lower().endswith(ALLOWED_EXT):
        raise ValidationProblem(f"Unsupported file type for {safe}. Upload PDF or text documents.")
    if len(data) > settings.max_upload_bytes:
        raise ValidationProblem(f"{safe} is larger than {settings.max_upload_bytes // (1024 * 1024)} MB.")
    if not data:
        raise ValidationProblem(f"{safe} is empty.")
    digest = hashlib.sha256(data).hexdigest()
    folder = settings.storage_dir / claim.claim_number
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest[:12]}_{safe}"
    path.write_bytes(data)
    try:
        text, pages = docai.extract_text(safe, data)
    except Exception as exc:  # noqa: BLE001 - corrupt PDFs surface as a validation problem
        raise ValidationProblem(f"Could not read {safe}: {exc}") from exc
    doc = ClaimDocument(claim_id=claim.id, filename=safe, storage_path=str(path), sha256=digest, text=text,
                        pages=pages, doc_type=docai.classify(text, safe), status="EXTRACTED")
    db.add(doc)
    db.flush()
    facts = docai.extract_facts(text)
    for f in facts:
        db.add(ClaimFact(claim_id=claim.id, document_id=doc.id, name=f.name, value=f.value, confidence=f.confidence,
                         source_line=f.line, source_text=f.source))
        if f.name == "incident_date" and claim.incident_date is None:
            try:
                claim.incident_date = date.fromisoformat(f.value)
            except ValueError:
                pass
        if f.name == "claimed_amount" and claim.claimed_amount is None:
            claim.claimed_amount = Decimal(f.value)
    if claim.status in ("SUBMITTED", "DRAFT"):
        claim.status = "DOCUMENTS_RECEIVED"
    audit.log(db, claim.id, "DOCUMENT_UPLOADED", actor, {"filename": safe, "doc_type": doc.doc_type,
                                                         "sha256": digest, "facts_extracted": len(facts)})
    db.flush()
    return doc


def load_terms(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
