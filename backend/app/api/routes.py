"""REST API v1 (blueprint PART 12)."""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from .. import analytics, letters, llm, provenance, sla
from ..agents import audit
from ..agents.review import ACTIONS, apply_review
from ..agents.supervisor import analyze_claim
from ..auth import WRITE_ROLES, current_user, issue_token, supervisor, throttle, user_view, verify_password, writer
from ..config import REPO_ROOT, settings
from ..db import get_db
from ..models import (
    AgentRun,
    AnalysisRun,
    AuditEvent,
    Claim,
    ClaimDecision,
    ClaimFact,
    InsuredPolicy,
    Policy,
    PolicyIngestion,
    PolicyVersion,
    User,
    WorkflowTask,
)
from ..rag import service as rag
from ..services import IngestionFailed, ValidationProblem, add_document, ingest_policy_file

public = APIRouter(prefix="/api/v1")
router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_user)])


def _claim(db: Session, claim_number: str) -> Claim:
    c = db.query(Claim).filter_by(claim_number=claim_number).first()
    if c is None:
        raise HTTPException(404, f"Claim {claim_number} not found")
    return c


def _money(x) -> str | None:
    return None if x is None else str(Decimal(x).quantize(Decimal("0.01")))


# ------------------------------------------------------------------ health
@public.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "version": settings.version}


@public.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    clauses = rag.retrieve(db, "deductible", k=1)
    return {"status": "ready", "database": "ok", "policy_index": "ok" if clauses else "empty",
            "llm": "anthropic" if llm.enabled() else "disabled (extractive answers)",
            "database_backend": db.bind.dialect.name}


# -------------------------------------------------------------------- auth
class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=1, max_length=200)


@public.post("/auth/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    username = body.username.strip().lower()
    key = f"{request.client.host if request.client else '-'}|{username}"
    wait = throttle.retry_after(key)
    if wait:
        audit.log(db, None, "LOGIN_THROTTLED", username[:60], {"retry_after_s": wait})
        db.commit()
        raise HTTPException(429, f"Too many failed sign-ins. Try again in {wait} seconds.", headers={"Retry-After": str(wait)})
    user = db.query(User).filter_by(username=username, active=True).first()
    if user is None or not verify_password(body.password, user.password_hash):
        throttle.fail(key)
        audit.log(db, None, "LOGIN_FAILED", username[:60], {})
        db.commit()
        raise HTTPException(401, "Wrong username or password")
    throttle.reset(key)
    audit.log(db, None, "LOGIN", user.username, {"role": user.role})
    db.commit()
    return {"token": issue_token(user), "user": user_view(user)}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_view(user)


# ------------------------------------------------------------------ claims
class ClaimIn(BaseModel):
    policy_number: str = Field(min_length=3, max_length=40)
    claim_type: str = Field(pattern="^(health|motor)$")
    claimant_name: str = Field(min_length=2, max_length=200)
    incident_date: date | None = None
    claimed_amount: Decimal | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=4000)


def _clock(db: Session, c: Claim) -> dict:
    run = db.query(AnalysisRun).filter_by(claim_id=c.id, status="SUCCEEDED").order_by(AnalysisRun.id.desc()).first()
    terms = db.get(PolicyVersion, run.policy_version_id).terms if run and run.policy_version_id else None
    final = db.query(ClaimDecision).filter_by(claim_id=c.id, source="HUMAN").order_by(ClaimDecision.id.desc()).first()
    return sla.settlement_clock(c, terms, final)


def _claim_summary(c: Claim, ai: ClaimDecision | None, risk: str | None, clock: dict | None = None) -> dict:
    return {"settlement": clock,"claim_number": c.claim_number, "policy_number": c.policy_number, "claim_type": c.claim_type,
            "claimant_name": c.claimant_name, "incident_date": c.incident_date, "claimed_amount": _money(c.claimed_amount),
            "status": c.status, "created_at": c.created_at, "updated_at": c.updated_at,
            "recommendation": ai.decision if ai else None, "recommended_payable": _money(ai.payable_amount) if ai else None,
            "risk_level": risk, "documents": len(c.documents)}


@router.post("/claims", status_code=201)
def create_claim(body: ClaimIn, db: Session = Depends(get_db), user: User = Depends(writer)):
    if db.query(InsuredPolicy).filter_by(policy_number=body.policy_number).first() is None:
        raise HTTPException(422, f"Policy number {body.policy_number} is not in the policy register")
    n = (db.query(func.count(Claim.id)).scalar() or 0) + 1
    prefix = "CLM-H" if body.claim_type == "health" else "CLM-M"
    number = f"{prefix}-{3000 + n}"
    while db.query(Claim).filter_by(claim_number=number).first():
        n += 1
        number = f"{prefix}-{3000 + n}"
    c = Claim(claim_number=number, **body.model_dump())
    db.add(c)
    db.flush()
    audit.log(db, c.id, "CLAIM_CREATED", user.username, {"policy_number": c.policy_number, "claim_type": c.claim_type})
    db.commit()
    return _claim_summary(c, None, None)


@router.get("/claims")
def list_claims(status: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Claim)
    if status:
        query = query.filter(Claim.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter((Claim.claim_number.ilike(like)) | (Claim.claimant_name.ilike(like)) | (Claim.policy_number.ilike(like)))
    claims = query.order_by(Claim.id.desc()).all()
    ai = {d.claim_id: d for d in db.query(ClaimDecision).filter_by(source="AI").order_by(ClaimDecision.id).all()}
    risk = {}
    for r in db.query(AnalysisRun).filter_by(status="SUCCEEDED").order_by(AnalysisRun.id).all():
        risk[r.claim_id] = r.result["risk"]["level"] if r.result else None
    return [_claim_summary(c, ai.get(c.id), risk.get(c.id), _clock(db, c)) for c in claims]


EXPORT_FIELDS = ["claim_number", "claim_type", "policy_number", "claimant_name", "incident_date", "claimed_amount",
                 "recommendation", "recommended_payable", "risk_level", "status", "settlement_due", "settlement_state", "created_at"]


@router.get("/claims-export.csv")
def export_claims(db: Session = Depends(get_db)):
    rows = list_claims(None, None, db)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({**r, "settlement_due": r["settlement"]["due_date"], "settlement_state": r["settlement"]["state"]})
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=claim-sense-claims.csv"})


def _analysis(db: Session, c: Claim) -> dict | None:
    run = db.query(AnalysisRun).filter_by(claim_id=c.id).order_by(AnalysisRun.id.desc()).first()
    if run is None:
        return None
    agents = db.query(AgentRun).filter_by(analysis_run_id=run.id).order_by(AgentRun.id).all()
    return {"run_id": run.id, "correlation_id": run.correlation_id, "status": run.status, "error": run.error,
            "started_at": run.started_at, "finished_at": run.finished_at, "rules_version": run.rules_version,
            "agents": [{"agent": a.agent, "status": a.status, "summary": a.summary, "tool_calls": a.tool_calls,
                        "duration_ms": a.duration_ms} for a in agents],
            "result": run.result}


@router.get("/claims/{claim_number}")
def get_claim(claim_number: str, db: Session = Depends(get_db)):
    c = _claim(db, claim_number)
    decisions = db.query(ClaimDecision).filter_by(claim_id=c.id).order_by(ClaimDecision.id).all()
    task = db.query(WorkflowTask).filter_by(claim_id=c.id).order_by(WorkflowTask.id.desc()).first()
    events = db.query(AuditEvent).filter_by(claim_id=c.id).order_by(AuditEvent.id).all()
    facts = db.query(ClaimFact).filter_by(claim_id=c.id).order_by(ClaimFact.id).all()
    analysis = _analysis(db, c)
    ai = next((d for d in reversed(decisions) if d.source == "AI"), None)
    risk = analysis["result"]["risk"]["level"] if analysis and analysis["result"] else None
    return {
        **_claim_summary(c, ai, risk, _clock(db, c)), "description": c.description,
        "documents": [{"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "pages": d.pages, "status": d.status,
                       "sha256": d.sha256, "uploaded_at": d.uploaded_at} for d in c.documents],
        "facts": [{"id": f.id, "document_id": f.document_id, "name": f.name, "value": f.value, "confidence": f.confidence,
                   "line": f.source_line, "source_text": f.source_text} for f in facts],
        "analysis": analysis,
        "decisions": [{"id": d.id, "source": d.source, "decision": d.decision, "payable_amount": _money(d.payable_amount),
                       "actor": d.actor, "notes": d.notes, "created_at": d.created_at} for d in decisions],
        "workflow_task": {"id": task.id, "queue": task.queue, "priority": task.priority, "status": task.status,
                          "assignee": task.assignee, "created_at": task.created_at} if task else None,
        "audit": [{"id": e.id, "event_type": e.event_type, "actor": e.actor, "details": e.details,
                   "correlation_id": e.correlation_id, "created_at": e.created_at} for e in events],
    }


@router.get("/claims/{claim_number}/letter")
def claim_letter(claim_number: str, db: Session = Depends(get_db)):
    letter = letters.build_letter(db, _claim(db, claim_number))
    if letter is None:
        raise HTTPException(409, "Run the analysis before generating a letter")
    return letter


@router.post("/claims/{claim_number}/documents", status_code=201)
async def upload_documents(claim_number: str, files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                           user: User = Depends(writer)):
    c = _claim(db, claim_number)
    if c.status in ("APPROVED", "REJECTED"):
        raise HTTPException(409, "Claim is closed; documents can no longer be added")
    out = []
    for f in files:
        data = await f.read()
        try:
            d = add_document(db, c, f.filename or "upload.txt", data, actor=user.username)
        except ValidationProblem as exc:
            db.rollback()
            raise HTTPException(422, str(exc)) from exc
        n_facts = db.query(ClaimFact).filter_by(document_id=d.id).count()
        out.append({"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "pages": d.pages, "facts_extracted": n_facts})
    db.commit()
    return out


@router.get("/claims/{claim_number}/documents/{doc_id}")
def get_document(claim_number: str, doc_id: int, db: Session = Depends(get_db)):
    c = _claim(db, claim_number)
    d = next((d for d in c.documents if d.id == doc_id), None)
    if d is None:
        raise HTTPException(404, "Document not found")
    return {"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "pages": d.pages, "text": d.text}


@router.post("/claims/{claim_number}/analyze")
def analyze(claim_number: str, db: Session = Depends(get_db), user: User = Depends(writer)):
    c = _claim(db, claim_number)
    if c.status in ("APPROVED", "REJECTED"):
        raise HTTPException(409, "Claim already decided; reopen is not supported in this version")
    analyze_claim(db, c, actor=user.username)
    return _analysis(db, c)


@router.get("/claims/{claim_number}/analysis")
def get_analysis(claim_number: str, db: Session = Depends(get_db)):
    c = _claim(db, claim_number)
    a = _analysis(db, c)
    if a is None:
        raise HTTPException(404, "Claim has not been analysed yet")
    return a


class ReviewIn(BaseModel):
    action: str
    notes: str = Field(default="", max_length=4000)
    payable_amount: Decimal | None = Field(default=None, ge=0)


@router.post("/claims/{claim_number}/review")
def review_claim(claim_number: str, body: ReviewIn, db: Session = Depends(get_db), user: User = Depends(writer)):
    c = _claim(db, claim_number)
    if body.action not in ACTIONS:
        raise HTTPException(422, f"action must be one of {', '.join(ACTIONS)}")
    if c.status in ("APPROVED", "REJECTED"):
        raise HTTPException(409, f"Claim already {c.status.lower()}")
    ai = db.query(ClaimDecision).filter_by(claim_id=c.id, source="AI").order_by(ClaimDecision.id.desc()).first()
    if ai is None:
        raise HTTPException(409, "Run the AI analysis before recording a decision")
    if body.action in ("REJECT", "ESCALATE", "INVESTIGATE") and not body.notes.strip():
        raise HTTPException(422, "Notes are required to reject, escalate or refer for investigation")
    if c.status == "ESCALATED" and user.role != "SUPERVISOR":
        raise HTTPException(403, "This claim is escalated; a supervisor must decide it")
    task = db.query(WorkflowTask).filter_by(claim_id=c.id, status="OPEN").first()
    if task and task.assignee not in (None, user.display_name) and user.role != "SUPERVISOR":
        raise HTTPException(409, f"This review is assigned to {task.assignee}; a supervisor can reassign it")
    if body.action == "APPROVE" and user.approval_limit is not None:
        amount = body.payable_amount if body.payable_amount is not None else ai.payable_amount
        if amount is not None and Decimal(amount) > user.approval_limit:
            raise HTTPException(403, f"₹{Decimal(amount):,.2f} is above your approval limit of ₹{user.approval_limit:,.2f}. "
                                     "Escalate it to a supervisor.")
    d = apply_review(db, c, body.action, user.display_name, body.notes, body.payable_amount, ai.payable_amount)
    db.commit()
    return {"claim_number": c.claim_number, "status": c.status, "decision": d.decision,
            "payable_amount": _money(d.payable_amount)}


@router.get("/reviews")
def review_queue(db: Session = Depends(get_db)):
    tasks = db.query(WorkflowTask).filter_by(status="OPEN").order_by(WorkflowTask.id).all()
    order = {"HIGH": 0, "MEDIUM": 1, "NORMAL": 2}
    now = datetime.now(timezone.utc)
    out = []
    for t in sorted(tasks, key=lambda t: (order.get(t.priority, 9), t.id)):
        c = db.get(Claim, t.claim_id)
        ai = db.query(ClaimDecision).filter_by(claim_id=c.id, source="AI").order_by(ClaimDecision.id.desc()).first()
        run = db.query(AnalysisRun).filter_by(claim_id=c.id, status="SUCCEEDED").order_by(AnalysisRun.id.desc()).first()
        opened = t.created_at if t.created_at.tzinfo else t.created_at.replace(tzinfo=timezone.utc)
        out.append({"task_id": t.id, "queue": t.queue, "priority": t.priority, "assignee": t.assignee,
                    "created_at": t.created_at, "age_hours": round((now - opened).total_seconds() / 3600, 1),
                    "claim_number": c.claim_number, "claimant_name": c.claimant_name,
                    "claim_type": c.claim_type, "claimed_amount": _money(c.claimed_amount), "status": c.status,
                    "risk_level": run.result["risk"]["level"] if run and run.result else None,
                    "recommendation": ai.decision if ai else None,
                    "recommended_payable": _money(ai.payable_amount) if ai else None,
                    "settlement": _clock(db, c)})
    return out


@router.get("/reviewers")
def reviewers(db: Session = Depends(get_db)):
    return [{"username": u.username, "display_name": u.display_name, "role": u.role}
            for u in db.query(User).filter(User.active.is_(True), User.role.in_(WRITE_ROLES)).order_by(User.id).all()]


class AssignIn(BaseModel):
    username: str | None = Field(default=None, max_length=60)


@router.post("/reviews/{task_id}/assign")
def assign_task(task_id: int, body: AssignIn, db: Session = Depends(get_db), user: User = Depends(writer)):
    """Take, hand over or release an open review task. Adjusters take and release their own; supervisors reassign."""
    t = db.get(WorkflowTask, task_id)
    if t is None:
        raise HTTPException(404, f"Review task {task_id} not found")
    if t.status != "OPEN":
        raise HTTPException(409, f"Review task {task_id} is {t.status.lower()}")
    target = None
    if body.username is not None:
        target = db.query(User).filter_by(username=body.username, active=True).first()
        if target is None or target.role not in WRITE_ROLES:
            raise HTTPException(422, f"{body.username} is not a reviewer")
    if user.role != "SUPERVISOR":
        if target is not None and target.id != user.id:
            raise HTTPException(403, "Only a supervisor can assign a task to someone else")
        if t.queue == "SUPERVISOR_REVIEW" and target is not None:
            raise HTTPException(403, "This task is in the supervisor queue")
        if t.assignee not in (None, user.display_name):
            raise HTTPException(409, f"Assigned to {t.assignee}; a supervisor can reassign it")
    before, t.assignee = t.assignee, target.display_name if target else None
    claim = db.get(Claim, t.claim_id)
    audit.log(db, claim.id, "TASK_ASSIGNED" if target else "TASK_RELEASED", user.username,
              {"task_id": t.id, "queue": t.queue, "from": before, "to": t.assignee})
    db.commit()
    return {"task_id": t.id, "claim_number": claim.claim_number, "queue": t.queue, "assignee": t.assignee}


# ---------------------------------------------------------------- policies
@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    return [{"product_code": p.product_code, "name": p.name, "line_of_business": p.line_of_business,
             "insurer": p.insurer, "synthetic": p.synthetic,
             "versions": [{"id": v.id, "version": v.version, "effective_from": v.effective_from,
                           "effective_to": v.effective_to, "clauses": len(v.clauses), "source_file": v.source_file}
                          for v in p.versions]} for p in db.query(Policy).order_by(Policy.product_code).all()]


def _ingestion_view(r: PolicyIngestion) -> dict:
    return {"id": r.id, "filename": r.filename, "file_type": r.file_type, "sha256": r.sha256, "size_bytes": r.size_bytes,
            "status": r.status, "stages": r.stages, "product_code": r.product_code, "version": r.version, "pages": r.pages,
            "clauses": r.clauses, "warnings": r.warnings, "error": r.error, "actor": r.actor, "created_at": r.created_at,
            "finished_at": r.finished_at}


@router.post("/policies", status_code=201)
async def upload_policy(wording: UploadFile = File(...), terms: UploadFile = File(...), db: Session = Depends(get_db),
                        user: User = Depends(supervisor)):
    """Ingest a policy wording (PDF, Markdown or text) with its structured terms (JSON)."""
    try:
        t = json.loads((await terms.read()).decode("utf-8"))
        if not isinstance(t, dict):
            raise ValueError("terms must be a JSON object")
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(422, f"Structured terms are not valid JSON: {exc}") from exc
    try:
        rec = ingest_policy_file(db, wording.filename or "policy", await wording.read(), t, actor=user.username)
    except IngestionFailed as exc:
        db.commit()  # keep the FAILED ingestion record and its audit event
        raise HTTPException(422, f"Ingestion #{exc.record.id} failed: {exc}") from exc
    db.commit()
    rag.rebuild_index(db)
    return {"product_code": rec.product_code, "version": rec.version, "clauses": rec.clauses, "ingestion": _ingestion_view(rec)}


@router.get("/policy-ingestions")
def policy_ingestions(db: Session = Depends(get_db)):
    return [_ingestion_view(r) for r in db.query(PolicyIngestion).order_by(PolicyIngestion.id.desc()).limit(50).all()]


def _policy(db: Session, code: str) -> Policy:
    p = db.query(Policy).filter_by(product_code=code).first()
    if p is None:
        raise HTTPException(404, f"Policy {code} not found")
    return p


@router.get("/policies/{product_code}")
def get_policy(product_code: str, db: Session = Depends(get_db)):
    return next(p for p in list_policies(db) if p["product_code"] == _policy(db, product_code).product_code)


@router.get("/policies/{product_code}/versions")
def policy_versions(product_code: str, db: Session = Depends(get_db)):
    p = _policy(db, product_code)
    return [{"id": v.id, "version": v.version, "effective_from": v.effective_from, "effective_to": v.effective_to,
             "terms": v.terms,
             "clauses": [{"id": c.id, "clause_ref": c.clause_ref, "title": c.title, "section": c.section,
                          "page": c.page, "text": c.text} for c in v.clauses]} for v in p.versions]


@router.get("/insured-policies")
def insured_policies(db: Session = Depends(get_db)):
    return [{"policy_number": p.policy_number, "product_code": p.policy.product_code, "holder_name": p.holder_name,
             "start_date": p.start_date, "end_date": p.end_date, "sum_insured": _money(p.sum_insured)}
            for p in db.query(InsuredPolicy).order_by(InsuredPolicy.policy_number).all()]


# --------------------------------------------------------------------- rag
class RagQuery(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    product_code: str | None = None
    version: str | None = None


@router.post("/rag/query")
def rag_query(body: RagQuery, db: Session = Depends(get_db), user: User = Depends(current_user)):
    vids = None
    if body.product_code:
        p = _policy(db, body.product_code)
        vs = [v for v in p.versions if body.version is None or v.version == body.version]
        if not vs:
            raise HTTPException(404, f"Version {body.version} not found for {body.product_code}")
        vids = {v.id for v in vs}
    result = rag.answer(db, body.question, vids)
    audit.log(db, None, "RAG_QUERY", user.username, {"question": body.question, "grounded": result["grounded"],
                                                  "citations": [c["clause_id"] for c in result["citations"]]})
    db.commit()
    return result


# ------------------------------------------------------------ audit, stats
@router.get("/audit")
def audit_log(claim_number: str | None = None, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    q = db.query(AuditEvent)
    if claim_number:
        q = q.filter(AuditEvent.claim_id == _claim(db, claim_number).id)
    events = q.order_by(AuditEvent.id.desc()).limit(limit).all()
    numbers = {c.id: c.claim_number for c in db.query(Claim).all()}
    return [{"id": e.id, "claim_number": numbers.get(e.claim_id), "event_type": e.event_type, "actor": e.actor,
             "details": e.details, "correlation_id": e.correlation_id, "created_at": e.created_at} for e in events]


@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    return analytics.dashboard(db)


@router.get("/evaluation")
def evaluation_report():
    """Latest golden evaluation report, produced by `python scripts/evaluate.py` and committed with the code."""
    path = REPO_ROOT / "reports" / "evaluation.json"
    if not path.exists():
        raise HTTPException(404, "No evaluation report yet. Run python scripts/evaluate.py.")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/datasets")
def datasets():
    """The source registry, validated now: required provenance fields and, for in-use sources, file checksums."""
    return provenance.load_registry()


@router.get("/knowledge-base/manifest")
def knowledge_base_manifest(db: Session = Depends(get_db)):
    """Every indexed policy chunk with its source file, version, page, section/clause and extraction run."""
    return provenance.rag_manifest(db)
