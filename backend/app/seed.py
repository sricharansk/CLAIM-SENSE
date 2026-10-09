"""Idempotent demo seeding: synthetic policies, policy contracts, golden claim packets and dataset register."""
from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from .agents.supervisor import analyze_claim
from .config import settings
from .models import Claim, DatasetSource, InsuredPolicy, Policy, PolicyVersion
from .rag import service as rag
from .services import add_document, ingest_policy_file, load_terms

log = logging.getLogger("claimsense.seed")


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
    rag.rebuild_index(db)

    src = settings.data_dir / "dataset_sources.json"
    if src.exists() and not db.query(DatasetSource).count():
        for d in json.loads(src.read_text(encoding="utf-8")):
            db.add(DatasetSource(**d))
        db.commit()

    claims_dir = settings.data_dir / "claims"
    scenarios = json.loads((claims_dir / "scenarios.json").read_text(encoding="utf-8"))
    for s in scenarios:
        if db.query(Claim).filter_by(claim_number=s["claim_number"]).first():
            continue
        claim = Claim(claim_number=s["claim_number"], policy_number=s["policy_number"], claim_type=s["claim_type"],
                      claimant_name=s["claimant_name"], description=s["description"], status="SUBMITTED")
        db.add(claim)
        db.flush()
        for name in s["documents"]:
            add_document(db, claim, name, (claims_dir / s["claim_number"] / name).read_bytes(), actor="seed")
        db.commit()
        created["claims"] += 1
        if analyze:
            analyze_claim(db, claim, actor="seed")
    log.info("seed complete: %s", created)
    return created
