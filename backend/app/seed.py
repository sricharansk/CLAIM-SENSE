"""Idempotent demo seeding: synthetic policies, policy contracts, golden claim packets and dataset register."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from . import provenance
from .agents.review import apply_review
from .agents.supervisor import analyze_claim
from .config import settings
from .models import (
    AgentRun,
    AnalysisRun,
    AuditEvent,
    Claim,
    ClaimDecision,
    DatasetSource,
    InsuredPolicy,
    Policy,
    PolicyIngestion,
    PolicyVersion,
    User,
    WorkflowTask,
)
from .rag import service as rag
from .services import add_document, ingest_policy_file, load_terms

log = logging.getLogger("claimsense.seed")


def _backfill_ingestion_runs(db: Session, pol_dir) -> None:
    """Databases created before ingestion runs were recorded have seeded versions with no run; record one from the
    same source file so their clauses keep resolvable provenance. Versions with no source file on disk stay out."""
    have = {r.policy_version_id for r in db.query(PolicyIngestion).filter_by(status="READY").all()}
    for v in db.query(PolicyVersion).all():
        path = pol_dir / v.source_file
        if v.id in have or not path.is_file():
            continue
        data = path.read_bytes()
        now = datetime.now(timezone.utc)
        db.add(PolicyIngestion(filename=v.source_file, file_type=path.suffix.lstrip("."), sha256=hashlib.sha256(data).hexdigest(),
                               size_bytes=len(data), status="READY", product_code=v.policy.product_code, version=v.version,
                               policy_version_id=v.id, pages=max((c.page for c in v.clauses), default=0),
                               clauses=len(v.clauses), warnings=[], actor="seed (backfill)", finished_at=now,
                               stages=[{"status": "READY", "at": now.isoformat(timespec="seconds"),
                                        "detail": "Provenance backfilled for a version ingested before runs were recorded"}]))
    db.commit()


def _sync_registry(db: Session) -> None:
    """Mirror the validated source registry into dataset_sources; entries without provenance are rejected."""
    reg = provenance.load_registry()
    for problem in reg["problems"]:
        log.warning("source registry: %s", problem)
    rows = [DatasetSource(name=s["name"][:200], publisher=s["publisher"][:200], year=str(s["publication_date"])[:20],
                          url=s["url"][:400], purpose=", ".join(s["intended_use"]), status=s["status"])
            for s in reg["sources"] if s["valid"]]
    current = [(d.name, d.status) for d in db.query(DatasetSource).order_by(DatasetSource.id).all()]
    if current != [(r.name, r.status) for r in rows]:
        db.query(DatasetSource).delete()
        db.add_all(rows)
        db.commit()


def seed(db: Session, analyze: bool = True) -> dict:
    pol_dir = settings.data_dir / "policies"
    created = {"policy_versions": 0, "claims": 0}
    for md in sorted(pol_dir.glob("*.md")):
        terms = load_terms(md.with_suffix(".terms.json"))
        policy = db.query(Policy).filter_by(product_code=terms["product_code"]).first()
        if policy and db.query(PolicyVersion).filter_by(policy_id=policy.id, version=terms["version"]).first():
            continue
        ingest_policy_file(db, md.name, md.read_bytes(), terms, actor="seed")
        created["policy_versions"] += 1
    for p in json.loads((pol_dir / "insured_policies.json").read_text(encoding="utf-8")):
        if db.query(InsuredPolicy).filter_by(policy_number=p["policy_number"]).first():
            continue
        prod = db.query(Policy).filter_by(product_code=p["product_code"]).one()
        db.add(InsuredPolicy(policy_number=p["policy_number"], policy_id=prod.id, holder_name=p["holder_name"],
                             start_date=date.fromisoformat(p["start_date"]), end_date=date.fromisoformat(p["end_date"]),
                             sum_insured=Decimal(p["sum_insured"])))
    db.commit()
    _backfill_ingestion_runs(db, pol_dir)
    rag.rebuild_index(db)
    _sync_registry(db)

    claims_dir = settings.data_dir / "claims"
    scenarios = json.loads((claims_dir / "scenarios.json").read_text(encoding="utf-8"))
    for s in scenarios:
        if _create_claim(db, s, claims_dir / s["claim_number"]) is None:
            continue
        created["claims"] += 1
        if analyze:
            analyze_claim(db, db.query(Claim).filter_by(claim_number=s["claim_number"]).one(), actor="seed")
    book = claims_dir / "demo_book.json"
    if book.is_file():
        for s in json.loads(book.read_text(encoding="utf-8")):
            claim = _create_claim(db, s, claims_dir / "demo_book" / s["claim_number"])
            if claim is None:
                continue
            created["claims"] += 1
            if analyze:
                _replay_demo_history(db, claim, s)
    log.info("seed complete: %s", created)
    return created


def _create_claim(db: Session, s: dict, folder) -> Claim | None:
    if db.query(Claim).filter_by(claim_number=s["claim_number"]).first():
        return None
    claim = Claim(claim_number=s["claim_number"], policy_number=s["policy_number"], claim_type=s["claim_type"],
                  claimant_name=s["claimant_name"], description=s["description"], status="SUBMITTED")
    db.add(claim)
    db.flush()
    for name in s["documents"]:
        add_document(db, claim, name, (folder / name).read_bytes(), actor="seed")
    db.commit()
    return claim


HISTORY_NOTE = "[Seeded demo history] "


def _replay_demo_history(db: Session, claim: Claim, s: dict) -> None:
    """Analyse a demo-book claim, then move its records back to the filing date in the book and replay the
    reviewer actions listed for it, so the dashboard has trends, ageing and settlement history to show.
    Every replayed decision goes through the normal review path and its note says it is seeded demo history."""
    filed = datetime.now(timezone.utc) - timedelta(days=s["age_days"])
    analyze_claim(db, claim, actor="seed")
    _move(db, claim, since={}, to=filed)
    for h in s.get("history", []):
        since = _marks(db)
        ai = (db.query(ClaimDecision).filter_by(claim_id=claim.id, source="AI").order_by(ClaimDecision.id.desc()).first())
        ai_payable = Decimal(ai.payable_amount) if ai and ai.payable_amount is not None else None
        override = ai_payable + Decimal(h["payable_delta"]) if h.get("payable_delta") and ai_payable is not None else None
        reviewer = db.query(User).filter_by(username=h["actor"]).one().display_name  # as the review API records it
        apply_review(db, claim, h["action"], reviewer, HISTORY_NOTE + (h.get("notes") or ""), override, ai_payable)
        db.commit()
        _move(db, claim, since=since, to=filed + timedelta(days=h["after_days"], hours=3))
    db.commit()


def _marks(db: Session) -> dict:
    """Highest ids before a step, so only the rows that step creates are moved."""
    top = lambda m: db.query(m.id).order_by(m.id.desc()).limit(1).scalar() or 0  # noqa: E731
    return {"decision": top(ClaimDecision), "audit": top(AuditEvent), "task": top(WorkflowTask)}


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _move(db: Session, claim: Claim, since: dict, to: datetime) -> None:
    """Set the timestamps of this claim's records created after `since` to `to` (keeping run durations)."""
    if not since:
        claim.created_at = to
        for d in claim.documents:
            d.uploaded_at = to
        for r in db.query(AnalysisRun).filter_by(claim_id=claim.id).all():
            shift = to - _utc(r.started_at)
            r.started_at += shift
            if r.finished_at:
                r.finished_at += shift
            for a in db.query(AgentRun).filter_by(analysis_run_id=r.id).all():
                a.started_at += shift
    for d in db.query(ClaimDecision).filter(ClaimDecision.claim_id == claim.id, ClaimDecision.id > since.get("decision", 0)):
        d.created_at = to
    for e in db.query(AuditEvent).filter(AuditEvent.claim_id == claim.id, AuditEvent.id > since.get("audit", 0)):
        e.created_at = to
    for t in db.query(WorkflowTask).filter_by(claim_id=claim.id).all():
        if t.id > since.get("task", 0):
            t.created_at = to
        if t.closed_at is not None and (not since or _utc(t.closed_at) > to):
            t.closed_at = to
    claim.updated_at = to
    db.commit()
