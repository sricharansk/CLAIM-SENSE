import json

from app.agents import document as docai
from app.agents.risk import level, score_features

from .conftest import DATA


def test_claim_form_fields_with_source_lines():
    text = (DATA / "claims" / "CLM-M-2001" / "claim_form.txt").read_text()
    facts = {f.name: f for f in docai.extract_facts(text)}
    assert docai.classify(text) == "claim_form"
    assert facts["policy_number"].value == "CS-MTR-25-001204"
    assert facts["incident_date"].value == "2025-09-18"
    assert facts["claimed_amount"].value == "73500.00"
    assert facts["engine_cc"].value == "1197"
    assert text.splitlines()[facts["policy_number"].line - 1].startswith("Policy Number")


def test_line_items_and_categories():
    text = (DATA / "claims" / "CLM-M-2001" / "repair_estimate.txt").read_text()
    facts = docai.extract_facts(text)
    items = [json.loads(f.value) for f in facts if f.name == "line_item"]
    cats = {i["description"]: i["category"] for i in items}
    assert cats["Rear Bumper (plastic) - replace"] == "parts_plastic"
    assert cats["Boot Lid Panel (metal) - replace"] == "parts_metal"
    assert cats["Rear Windshield Glass"] == "glass"
    assert next(f for f in facts if f.name == "document_total").value == "73500.00"


def test_pdf_text_extraction():
    data = (DATA / "claims" / "CLM-H-1001" / "hospital_bill.pdf").read_bytes()
    text, pages = docai.extract_text("hospital_bill.pdf", data)
    assert pages == 1 and docai.classify(text) == "hospital_bill"
    items = [json.loads(f.value) for f in docai.extract_facts(text) if f.name == "line_item"]
    assert len(items) == 6 and sum(i["amount"] for i in items) == 106600


def test_risk_levels():
    assert level(score_features({"amount_ratio": 0.1, "days_since_start": 400})[0]) == "LOW"
    assert level(score_features({"amount_ratio": 0.6, "days_since_start": 60})[0]) == "MEDIUM"
    s, sig = score_features({"amount_ratio": 0.9, "days_since_start": 50, "amount_gap": 0.05})
    assert level(s) == "HIGH" and {x["code"] for x in sig} == {"HIGH_AMOUNT_RATIO", "EARLY_CLAIM", "AMOUNT_MISMATCH"}
    assert level(score_features({"duplicate_of": "CLM-1"})[0]) == "HIGH"
