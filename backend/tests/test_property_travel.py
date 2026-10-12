import json
from decimal import Decimal

from app.adjudication import rules
from app.agents import document as docai

from .conftest import DATA, login, new_claim

HOME = json.loads((DATA / "policies" / "HOME-GUARD_2025.1.terms.json").read_text())
TRAVEL = json.loads((DATA / "policies" / "TRV-GLOBE_2025.1.terms.json").read_text())
D = Decimal


def items(*rows):
    return [rules.LineItem(desc, D(str(amt)), cat) for desc, amt, cat in rows]


def test_property_average_clause_matches_hand_calculation():
    li = items(("Plaster", 145000, "building_repair"), ("Platform", 98000, "building_repair"),
               ("Wiring", 42000, "building_repair"), ("Refrigerator", 58000, "contents_electronics"),
               ("Microwave", 14000, "contents_electronics"), ("Sofa", 66000, "contents_furniture"),
               ("Debris", 27000, "building_repair"))
    r = rules.adjudicate_property(li, D("450000"), HOME, D("2500000"), D("3000000"))
    # 450000 - depreciation (11600 + 2800 + 6600) = 429000; x 25/30 = 357500; - 10000 excess = 347500
    assert r.depreciation == D("21000.00")
    assert r.underinsurance == D("71500.00")
    assert r.deductible == D("10000.00")
    assert r.payable == D("347500.00")
    assert all(s.clause_ref for s in r.steps[1:])


def test_property_within_tolerance_has_no_average():
    # value at risk 15% over the sum insured is still within the tolerance in clause 2.3
    r = rules.adjudicate_property(items(("Roof", 50000, "building_repair")), D("50000"), HOME, D("1000000"), D("1150000"))
    assert r.underinsurance == D("0.00")
    assert r.payable == D("40000.00")


def test_property_valuables_not_payable():
    r = rules.adjudicate_property(items(("Gold jewellery", 140000, "valuables"), ("Laptop", 85000, "contents_electronics")),
                                  D("225000"), HOME, D("1200000"), None)
    assert r.non_covered == D("140000.00")
    assert r.payable == D("58000.00")  # 85000 - 20% = 68000 - 10000 excess


def test_travel_per_item_and_benefit_limits():
    li = items(("Suitcase", 18000, "baggage_item"), ("Laptop", 85000, "baggage_item"), ("Clothing", 24000, "baggage_item"),
               ("Camera", 40000, "baggage_item"), ("Shoes", 14000, "baggage_item"))
    r = rules.adjudicate_travel(li, D("181000"), TRAVEL, D("4000000"))
    # per item 25000: cuts 60000 + 15000 -> 106000; baggage limit 100000 cuts 6000; deductible 5000 -> 95000
    cuts = {s.rule_id: s.adjustment for s in r.steps}
    assert sum(s.adjustment for s in r.steps if s.rule_id == "R20_ITEM_LIMIT") == D("-75000.00")
    assert cuts["R20_BENEFIT_LIMIT"] == D("-6000.00")
    assert r.payable == D("95000.00")


def test_travel_medical_has_no_benefit_sub_limit():
    li = items(("Surgery", 300000, "medical_treatment"), ("Toiletries", 2000, "personal_comfort"))
    r = rules.adjudicate_travel(li, D("302000"), TRAVEL, D("4000000"))
    assert r.non_covered == D("2000.00")
    assert r.payable == D("295000.00")


def test_line_specific_categories():
    assert docai.categorize("Laptop Computer", "property")[0] == "contents_electronics"
    assert docai.categorize("Laptop Computer", "travel")[0] == "baggage_item"
    assert docai.categorize("Bedroom Wall Plaster and Repaint", "property")[0] == "building_repair"
    assert docai.categorize("Hotel Booking (non-refundable)", "travel")[0] == "trip_cancellation"
    # health and motor keep the original vocabulary
    assert docai.categorize("Rear Bumper (plastic) - replace")[0] == "parts_plastic"


def test_property_claim_extracts_value_at_risk(client):
    n = new_claim(client, "CLM-P-3001", "CS-HOM-25-003101", "property", "Anita Desai")
    r = client.get(f"/api/v1/claims/{n}/analysis").json()["result"]
    assert n.startswith("CLM-P-")
    assert r["facts"]["value_at_risk"] == "3000000.00"
    assert r["adjudication"]["underinsurance"] == "71500.00"
    assert r["adjudication"]["payable_amount"] == "347500.00"


def test_burglary_without_police_report_requests_information(client):
    n = client.post("/api/v1/claims", json={"policy_number": "CS-HOM-24-003145", "claim_type": "property",
                                             "claimant_name": "Vikram Singh"}).json()["claim_number"]
    folder = DATA / "claims" / "CLM-P-3002"
    files = [("files", (p.name, p.read_bytes(), "text/plain")) for p in sorted(folder.glob("*.txt")) if p.name != "police_report.txt"]
    assert client.post(f"/api/v1/claims/{n}/documents", files=files).status_code == 201
    client.post(f"/api/v1/claims/{n}/analyze")
    r = client.get(f"/api/v1/claims/{n}/analysis").json()["result"]
    assert r["coverage"]["missing_documents"] == ["police_report"]
    assert r["recommendation"]["decision"] == "REQUEST_INFO"


def test_travel_claim_outside_trip_is_not_covered(client):
    n = client.post("/api/v1/claims", json={"policy_number": "CS-TRV-25-004588", "claim_type": "travel",
                                             "claimant_name": "Kavya Reddy"}).json()["claim_number"]
    folder = DATA / "evaluation" / "packets" / "EVAL-T-02"
    files = [("files", (p.name, p.read_bytes(), "text/plain")) for p in sorted(folder.glob("*.txt"))]
    assert client.post(f"/api/v1/claims/{n}/documents", files=files).status_code == 201
    client.post(f"/api/v1/claims/{n}/analyze")
    r = client.get(f"/api/v1/claims/{n}/analysis").json()["result"]
    fail = next(f for f in r["coverage"]["findings"] if f["outcome"] == "FAIL")
    assert fail["code"] == "OUTSIDE_TRIP" and fail["citation"]["clause_ref"] == "1.3"
    assert r["risk"]["features"]["days_since_start"] is None  # trip-based cover: no early-claim signal
    assert r["recommendation"]["decision"] == "RECOMMEND_REJECT"


def test_claim_type_validation(client):
    h = login(client, "supervisor")
    r = client.post("/api/v1/claims", headers=h, json={"policy_number": "CS-TRV-25-004588", "claim_type": "marine",
                                                        "claimant_name": "Kavya Reddy"})
    assert r.status_code == 422


def test_value_at_risk_correction_is_validated_and_used(client):
    n = new_claim(client, "CLM-P-3001", "CS-HOM-25-003101", "property", "Anita Desai")
    bad = client.post(f"/api/v1/claims/{n}/facts", json={"name": "value_at_risk", "value": "abc", "reason": "typo"})
    assert bad.status_code == 422 and "non-negative amount" in bad.json()["error"]["message"]
    ok = client.post(f"/api/v1/claims/{n}/facts", json={"name": "value_at_risk", "value": "2,600,000",
                                                         "reason": "Surveyor revised the rebuilding cost"})
    assert ok.status_code in (200, 201), ok.text
    client.post(f"/api/v1/claims/{n}/analyze")
    adj = client.get(f"/api/v1/claims/{n}/analysis").json()["result"]["adjudication"]
    # 26 lakh is within 15% of the 25 lakh sum insured, so no average: 429000 - 10000 excess
    assert adj["underinsurance"] == "0.00" and adj["payable_amount"] == "419000.00"
