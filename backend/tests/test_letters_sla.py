from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app.letters import _inr
from app.sla import settlement_clock

from .conftest import login, new_claim


def test_rejection_letter_quotes_the_clause(client):
    letter = client.get("/api/v1/claims/CLM-H-1002/letter").json()
    assert letter["kind"] == "REPUDIATION" and letter["status"] == "DRAFT"
    assert letter["references"][0]["clause_ref"] == "3.3"
    assert any("Specified Diseases and Procedures" in p for p in letter["paragraphs"])
    assert any("cataract" in p for p in letter["paragraphs"])


def test_settlement_letter_uses_rules_engine_amounts(client):
    n = new_claim(client, "demo_upload", "CS-HLT-23-000089", "health", "Fatima Shaikh")
    client.post(f"/api/v1/claims/{n}/review", headers=login(client, "adjuster"), json={"action": "APPROVE"})
    letter = client.get(f"/api/v1/claims/{n}/letter").json()
    assert letter["kind"] == "SETTLEMENT" and letter["status"] == "FINAL"
    assert letter["signed_by"] == "Adjuster A. Rao"
    text = " ".join(letter["paragraphs"])
    assert "INR 64,080.00" in text and "INR 78,000.00" in text
    assert "Co-payment 10%: INR 7,120.00 (clause 5.2)" in text


def test_document_request_letter_lists_missing_documents(client):
    letter = client.get("/api/v1/claims/CLM-H-1004/letter").json()
    assert letter["kind"] == "DOCUMENT_REQUEST"
    assert "discharge summary" in letter["paragraphs"][0]


def test_investigation_letter_does_not_disclose_risk_signals(client):
    letter = client.get("/api/v1/claims/CLM-H-1006/letter").json()
    assert letter["kind"] == "UNDER_REVIEW"
    assert "duplicate" not in " ".join(letter["paragraphs"]).lower()


def test_inr_uses_indian_grouping():
    assert _inr("1234567.5") == "INR 12,34,567.50"
    assert _inr("999") == "INR 999.00"


def _claim(status, uploaded):
    return SimpleNamespace(status=status, created_at=uploaded, documents=[SimpleNamespace(uploaded_at=uploaded)])


def test_settlement_clock_states():
    terms = {"settlement_days": {"value": 30, "clause": "6.3"}}
    up = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert settlement_clock(_claim("PENDING_REVIEW", up), terms, None, date(2026, 1, 11))["state"] == "ON_TRACK"
    assert settlement_clock(_claim("PENDING_REVIEW", up), terms, None, date(2026, 1, 28))["state"] == "DUE_SOON"
    late = settlement_clock(_claim("PENDING_REVIEW", up), terms, None, date(2026, 2, 5))
    assert late["state"] == "OVERDUE" and late["days_left"] == -5 and late["due_date"] == date(2026, 1, 31)
    decided = SimpleNamespace(created_at=up + timedelta(days=40))
    assert settlement_clock(_claim("APPROVED", up), terms, decided)["state"] == "BREACHED"


def test_claims_carry_settlement_due_and_export_csv(client):
    c = client.get("/api/v1/claims/CLM-H-1001").json()
    assert c["settlement"]["days"] == 30 and c["settlement"]["clause"] == "6.3"
    r = client.get("/api/v1/claims-export.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0].startswith("claim_number,claim_type") and any(line.startswith("CLM-H-1001,") for line in lines)
