"""Application services shared by the API and the seeder: policy ingestion and document intake."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from .agents import audit
from .agents import document as docai
from .config import settings
from .models import Claim, ClaimDocument, ClaimFact, Policy, PolicyClause, PolicyIngestion, PolicyVersion
from .rag.parser import ClauseChunk, parse_policy_markdown, parse_policy_pages
from .safety import embedded_instructions


class ValidationProblem(ValueError):
    pass


REQUIRED_TERMS = ("product_code", "product_name", "line_of_business", "version", "effective_from", "effective_to",
                  "deductible", "required_documents")


class IngestionFailed(ValidationProblem):
    def __init__(self, record: PolicyIngestion, message: str):
        super().__init__(message)
        self.record = record


POLICY_TYPES = (".pdf", ".md", ".txt")


def _validate_terms(db: Session, terms: dict) -> None:
    missing = [k for k in REQUIRED_TERMS if k not in terms]
    if missing:
        raise ValidationProblem(f"Policy terms missing fields: {', '.join(missing)}")
    try:
        start, end = date.fromisoformat(terms["effective_from"]), date.fromisoformat(terms["effective_to"])
    except (TypeError, ValueError) as exc:
        raise ValidationProblem("effective_from and effective_to must be ISO dates (YYYY-MM-DD).") from exc
    if end < start:
        raise ValidationProblem("effective_to is before effective_from.")
    policy = db.query(Policy).filter_by(product_code=terms["product_code"]).first()
    if policy and db.query(PolicyVersion).filter_by(policy_id=policy.id, version=terms["version"]).first():
        raise ValidationProblem(f"{terms['product_code']} version {terms['version']} already exists.")


def _check_chunks(chunks: list[ClauseChunk], terms: dict) -> None:
    if not chunks:
        raise ValidationProblem("No clauses found. Use '## N. Section' and '### N.M Clause' headings "
                                "(or numbered 'N. Section' and 'N.M Clause' lines in a PDF).")
    if unknown := sorted(_clause_refs(terms) - {c.clause_ref for c in chunks}):
        raise ValidationProblem(f"Terms cite clauses that are not in the wording: {', '.join(unknown)}")


def ingest_policy(db: Session, markdown: str, terms: dict, source_file: str, actor: str = "system") -> PolicyVersion:
    _validate_terms(db, terms)
    chunks = parse_policy_markdown(markdown)
    _check_chunks(chunks, terms)
    return _store_version(db, chunks, terms, source_file, actor)


def ingest_policy_file(db: Session, filename: str, data: bytes, terms: dict, actor: str = "system") -> PolicyIngestion:
    """Policy ingestion pipeline: upload → validation → checksum → extraction (pages preserved) → clause parsing →
    version metadata → persistence → indexing. Every attempt is recorded with its processing states. Wording text
    is data: instruction-like lines are reported as warnings and never acted on."""
    safe = Path(filename or "policy").name[:200]
    rec = PolicyIngestion(filename=safe, file_type=Path(safe).suffix.lower().lstrip("."), sha256=hashlib.sha256(data).hexdigest(),
                          size_bytes=len(data), actor=actor, stages=[], warnings=[],
                          product_code=str(terms.get("product_code", ""))[:40] or None, version=str(terms.get("version", ""))[:20] or None)
    db.add(rec)

    def stage(status: str, detail: str) -> None:
        rec.status = status
        rec.stages = [*rec.stages, {"status": status, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "detail": detail}]

    stage("UPLOADED", f"{safe}, {len(data):,} bytes, sha256 {rec.sha256[:16]}")
    db.flush()
    try:
        stage("VALIDATING", "File type, size, checksum and structured terms")
        if not safe.lower().endswith(POLICY_TYPES):
            raise ValidationProblem(f"Unsupported file type for {safe}. Upload a PDF, Markdown or text wording.")
        if not data:
            raise ValidationProblem(f"{safe} is empty.")
        if len(data) > settings.max_upload_bytes:
            raise ValidationProblem(f"{safe} is larger than {settings.max_upload_bytes // (1024 * 1024)} MB.")
        seen = db.query(PolicyIngestion).filter_by(sha256=rec.sha256, status="READY").first()
        if seen:
            raise ValidationProblem(f"This exact file was already ingested as {seen.product_code} v{seen.version} (ingestion #{seen.id}).")
        _validate_terms(db, terms)

        stage("EXTRACTING", "Reading text with page numbers, then sections and clauses")
        if rec.file_type == "pdf":
            try:
                from pypdf import PdfReader
                pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]
            except Exception as exc:  # malformed or encrypted PDF
                raise ValidationProblem(f"Could not read the PDF: {exc}") from exc
            if not any(p.strip() for p in pages):
                raise ValidationProblem("The PDF has no text layer (scanned image?). OCR is not available in this build.")
            text, chunks = "\n".join(pages), parse_policy_pages(pages)
            rec.pages = len(pages)
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValidationProblem(f"{safe} is not UTF-8 text.") from exc
            chunks = parse_policy_markdown(text)
            rec.pages = max((c.page for c in chunks), default=0)
        _check_chunks(chunks, terms)
        rec.warnings = [f"line {h['line']}: {h['text']}" for h in embedded_instructions(text)]
        rec.clauses = len(chunks)

        stage("INDEXING", f"{len(chunks)} clauses on {rec.pages} pages; persisting version and indexing")
        v = _store_version(db, chunks, terms, safe, actor)
        rec.policy_version_id = v.id
        stage("READY", f"{v.policy.product_code} v{v.version} effective {v.effective_from} to {v.effective_to}"
              + (f"; {len(rec.warnings)} instruction-like lines ignored" if rec.warnings else ""))
    except ValidationProblem as exc:
        rec.error = str(exc)
        stage("FAILED", str(exc))
        rec.finished_at = datetime.now(timezone.utc)
        audit.log(db, None, "POLICY_INGESTION_FAILED", actor, {"ingestion_id": rec.id, "file": safe, "error": str(exc)})
        raise IngestionFailed(rec, str(exc)) from exc
    rec.finished_at = datetime.now(timezone.utc)
    return rec


def _store_version(db: Session, chunks: list[ClauseChunk], terms: dict, source_file: str, actor: str) -> PolicyVersion:
    policy = db.query(Policy).filter_by(product_code=terms["product_code"]).first()
    if policy is None:
        policy = Policy(product_code=terms["product_code"], name=terms["product_name"],
                        line_of_business=terms["line_of_business"], insurer=terms.get("insurer", ""))
        db.add(policy)
        db.flush()
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
