import json
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import seed as seeding
from app.config import settings
from app.db import Base, SessionLocal
from app.models import Claim, ClaimDecision
from app.rag import service as rag

from .conftest import DATA


def test_live_seed_files_every_evaluation_packet_with_the_golden_outcome(client, tmp_path, monkeypatch):
    """The deployed app seeds the packets as claims too; each must come out as the hand-worked golden case says."""
    cases = [c for c in json.loads((DATA / "evaluation" / "golden_cases.json").read_text())["claims"] if "packet" in c]
    assert len(cases) == 7 and all(c["seeded_as"] for c in cases)
    engine = create_engine(f"sqlite:///{tmp_path / 'live.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(settings, "seed_packets", True)
    try:
        with sessionmaker(bind=engine, expire_on_commit=False)() as db:
            assert seeding.seed(db)["claims"] == 50 + 7
            assert seeding.seed(db)["claims"] == 0  # idempotent
            for c in cases:
                claim = db.query(Claim).filter_by(claim_number=c["seeded_as"]).one()
                ai = db.query(ClaimDecision).filter_by(claim_id=claim.id, source="AI").one()
                assert (ai.decision, ai.payable_amount) == (c["expect"]["recommendation"],
                                                            Decimal(c["expect"]["payable_amount"])), c["id"]
    finally:
        with SessionLocal() as db:  # the retrieval index is shared: point it back at the test database
            rag.rebuild_index(db)
        engine.dispose()
