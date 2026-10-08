from app.rag.parser import parse_policy_markdown
from app.rag.retriever import HybridIndex

from .conftest import DATA


def test_parser_keeps_page_section_and_clause():
    chunks = parse_policy_markdown((DATA / "policies" / "HLT-SHIELD_2025.1.md").read_text())
    by_ref = {c.clause_ref: c for c in chunks}
    assert len(chunks) == 21
    assert by_ref["2.2"].page == 2 and by_ref["2.2"].section == "2. Coverage"
    assert "INR 5,000 per day" in by_ref["2.2"].text
    assert by_ref["4.3"].page == 4


def test_hybrid_index_ranks_exact_clause_first_and_filters_group():
    idx = HybridIndex()
    idx.build([(1, 10, "Room rent limit. Room rent payable up to INR 5,000 per day."),
               (2, 10, "Deductible. A deductible applies to each claim."),
               (3, 20, "Room rent limit. Room rent payable up to INR 4,000 per day.")])
    assert idx.search("room rent per day", k=1)[0].key in (1, 3)
    hits = idx.search("room rent per day", groups={20})
    assert [h.key for h in hits] == [3]
    assert idx.search("deductible")[0].key == 2


def test_rag_answer_is_cited(client):
    r = client.post("/api/v1/rag/query", json={"question": "What is the room rent limit per day?",
                                                "product_code": "HLT-SHIELD", "version": "2025.1"}).json()
    assert r["grounded"] is True
    top = r["citations"][0]
    assert (top["clause_ref"], top["page"], top["version"]) == ("2.2", 2, "2025.1")
    assert "§2.2" in r["answer"] and "5,000" in r["answer"]


def test_rag_synonym_expansion_finds_alcohol_exclusion(client):
    r = client.post("/api/v1/rag/query", json={"question": "Is drunk driving covered?", "product_code": "MTR-SECURE"}).json()
    assert r["citations"][0]["clause_ref"] == "3.1"


def test_rag_refuses_without_evidence(client):
    r = client.post("/api/v1/rag/query", json={"question": "What is the capital of France?"}).json()
    assert r["grounded"] is False and r["mode"] == "refusal"
