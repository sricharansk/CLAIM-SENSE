"""Source registry validation (Data Prompt A) and the RAG ingestion manifest (Data Prompt G)."""
import copy
import json
from datetime import date

from fastapi.testclient import TestClient

from app import provenance
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Policy, PolicyClause, PolicyIngestion, PolicyVersion
from app.rag import service as rag
from app.seed import _backfill_ingestion_runs

from .conftest import DATA


def _registry() -> dict:
    return json.loads((DATA / "source_registry.json").read_text(encoding="utf-8"))


def test_committed_registry_has_complete_provenance():
    reg = provenance.load_registry()
    assert reg["valid"], reg["problems"]
    in_use = [s for s in reg["sources"] if s["status"] == "IN_USE"]
    assert in_use and all(s["checksum_sha256"] and s["license"] != "CHECK_SOURCE" for s in in_use)
    assert all(s["url"].startswith("https://") for s in reg["sources"] if s["status"] == "REGISTERED")


def test_validator_rejects_missing_or_wrong_provenance(tmp_path):
    base = _registry()
    synthetic = next(s for s in base["sources"] if s["id"] == "synthetic-claims-portfolio")
    external = next(s for s in base["sources"] if s["status"] == "REGISTERED")

    def problems(**changes):
        reg = copy.deepcopy(base)
        reg["sources"] = [{**copy.deepcopy(synthetic), **changes}]
        return provenance.validate_registry(reg)["problems"]

    assert problems() == []
    assert any("missing publication_date" in p for p in problems(publication_date=None))
    assert any("missing license" in p for p in problems(license=""))
    assert any("licence or terms confirmed" in p for p in problems(license="CHECK_SOURCE"))
    assert any("retrieval or generation date" in p for p in problems(retrieval_date=None))
    assert any("checksum does not match" in p for p in problems(checksum_sha256="0" * 64))
    assert any("files not found" in p for p in problems(paths=["data/nope.csv"]))
    assert any("YYYY" in p for p in problems(publication_date="Oct 2026"))
    assert any("unknown intended_use" in p for p in problems(intended_use=["training"]))

    reg = copy.deepcopy(base)
    reg["sources"] = [{**external, "url": "http://example.org", "paths": ["data/claims"]}, external, external]
    found = provenance.validate_registry(reg)["problems"]
    assert any("https URL" in p for p in found) and any("not downloaded" in p for p in found)
    assert any(p.startswith("duplicate id") for p in found)

    # the checksum covers every file under a listed directory
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "a.txt").write_text("one")
    before = provenance.tree_sha256(tmp_path, ["d"])
    (tmp_path / "d" / "b.txt").write_text("two")
    assert provenance.tree_sha256(tmp_path, ["d"]) != before


def test_datasets_endpoint_serves_validated_registry(client):
    body = client.get("/api/v1/datasets").json()
    assert body["valid"] and len(body["sources"]) == len(_registry()["sources"])
    assert all(s["valid"] for s in body["sources"])
    with TestClient(app) as anon:
        assert anon.get("/api/v1/datasets").status_code == 401


def test_every_indexed_chunk_resolves_to_its_source(client):
    m = client.get("/api/v1/knowledge-base/manifest").json()
    assert m["indexed_chunks"] == len(m["chunks"]) > 0 and m["rejected"] == []
    runs = {d["document"]: d["extraction_run"] for d in m["documents"]}
    assert {"HLT-SHIELD@2024.1", "HLT-SHIELD@2025.1", "MTR-SECURE@2025.1"} <= set(runs)
    assert len({c["chunk_id"] for c in m["chunks"]}) == len(m["chunks"])
    for c in m["chunks"]:
        assert c["source_file"] and c["page"] >= 1 and c["section"] and c["clause_ref"]
        assert c["extraction_run"] == runs[c["document"]] and len(c["text_sha256"]) == 64


def test_chunk_without_provenance_is_rejected_from_the_index(client):
    with SessionLocal() as db:
        p = Policy(product_code="ORPHAN", name="Orphan wording", line_of_business="health", insurer="")
        db.add(p)
        db.flush()
        v = PolicyVersion(policy_id=p.id, version="1", effective_from=date(2025, 1, 1), effective_to=date(2025, 12, 31),
                          source_file="orphan.md", terms={})
        db.add(v)
        db.flush()
        db.add(PolicyClause(version_id=v.id, clause_ref="1.1", title="Zygomycosis cover", section="1. Cover", page=1,
                            text="Zygomycosis treatment is covered in full."))
        db.commit()
        try:
            rag.rebuild_index(db)
            m = provenance.rag_manifest(db)
            assert [(r["product_code"], r["missing"]) for r in m["rejected"]] == [("ORPHAN", ["extraction run"])]
            assert not any(h["product_code"] == "ORPHAN" for h in rag.retrieve(db, "zygomycosis treatment"))
        finally:
            db.query(PolicyClause).filter_by(version_id=v.id).delete()
            db.delete(v)
            db.delete(p)
            db.commit()
            rag.rebuild_index(db)


def test_seed_backfills_a_missing_extraction_run(client):
    with SessionLocal() as db:
        v = (db.query(PolicyVersion).join(Policy).filter(Policy.product_code == "HLT-SHIELD", PolicyVersion.version == "2024.1")
             .one())
        original = db.query(PolicyIngestion).filter_by(policy_version_id=v.id, status="READY").one()
        original.policy_version_id = None  # as in a database created before runs were recorded
        db.commit()
        try:
            _backfill_ingestion_runs(db, settings.data_dir / "policies")
            run = db.query(PolicyIngestion).filter_by(policy_version_id=v.id, status="READY").one()
            assert run.actor == "seed (backfill)" and run.sha256 == original.sha256 and run.clauses == 21
        finally:
            db.query(PolicyIngestion).filter_by(policy_version_id=v.id, actor="seed (backfill)").delete()
            original.policy_version_id = v.id
            db.commit()
            rag.rebuild_index(db)
