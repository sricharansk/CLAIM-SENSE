"""Travel, home, personal accident and life: the indemnity and benefit-schedule rules worked by hand, the line check
on new claims, and each line's sample packet run through the real pipeline."""
import json
from decimal import Decimal

import pytest

from app.adjudication.rules import LineItem, adjudicate_benefits, adjudicate_indemnity, money

from .conftest import DATA, login


def terms(name: str) -> dict:
    return json.loads((DATA / "policies" / f"{name}_2026.1.terms.json").read_text(encoding="utf-8"))


def steps(r) -> list[tuple[str, Decimal]]:
    return [(s.rule_id, s.adjustment) for s in r.steps]


def test_travel_baggage_depreciation_item_limit_and_delay_cap():
    # Suitcase 40,000 less 10% = 36,000, above the 15,000 per-item limit (clause 2.3): 15,000.
    # Tablet 12,000 less 10% = 10,800. Trip delay 12,500 capped at 10,000 (clause 2.4).
    # 64,500 - 5,200 - 21,000 - 2,500 = 35,800; the 5,000 deductible applies to medical expenses only.
    items = [LineItem("Checked baggage - suitcase", money(40000), "baggage"),
             LineItem("Checked baggage - tablet", money(12000), "baggage"),
             LineItem("Trip delay - hotel and meals", money(12500), "trip_delay")]
    r = adjudicate_indemnity(items, money(64500), terms("TRV-GLOBE"), money(1000000), sum_insured=money(1000000))
    assert r.depreciation == money(5200) and r.deductible == 0 and r.payable == money(35800)
    assert ("R20_ITEM_LIMIT", money(-21000)) in steps(r) and ("R22_CATEGORY_LIMIT", money(-2500)) in steps(r)
    assert "R30_DEDUCTIBLE" not in [s.rule_id for s in r.steps]


def test_travel_deductible_applies_to_medical_expenses():
    items = [LineItem("Hospital room", money(20000), "room_rent"), LineItem("Checked baggage", money(5000), "baggage")]
    r = adjudicate_indemnity(items, money(25000), terms("TRV-GLOBE"), money(1000000), sum_insured=money(1000000))
    assert r.deductible == money(5000) and r.payable == money(20000 + 4500 - 5000)


def test_home_average_clause_scales_the_loss_by_sum_insured_over_value_at_risk():
    # TV 80,000 less 15% = 68,000; jewellery 150,000 capped at 100,000 (clause 2.3); assessed 168,000.
    # Insured for 25 lakh against 50 lakh at risk: average clause (1.3) pays half, 84,000; deductible 10,000.
    items = [LineItem("Television (electronics)", money(80000), "contents_electronics"),
             LineItem("Gold bangles (jewellery)", money(150000), "jewellery")]
    r = adjudicate_indemnity(items, money(230000), terms("HOME-SHIELD"), money(2500000), money(5000000), money(2500000))
    assert ("R45_AVERAGE", money(-84000)) in steps(r)
    assert r.depreciation == money(12000) and r.deductible == money(10000) and r.payable == money(74000)


def test_home_average_clause_uses_the_full_sum_insured_not_what_is_left():
    # An earlier claim used 15 lakh of the 25 lakh; the property is still fully insured, so no average applies.
    items = [LineItem("Sofa (furniture)", money(50000), "contents_furniture")]
    r = adjudicate_indemnity(items, money(50000), terms("HOME-SHIELD"), money(1000000), money(2400000), money(2500000))
    assert "R45_AVERAGE" not in [s.rule_id for s in r.steps] and r.payable == money(45000 - 10000)


def test_personal_accident_pays_the_schedule_not_the_amount_claimed():
    # Thumb: 25% of 5 lakh = 125,000 (+25,000). TTD: 3 weeks x min(1% of 5 lakh, 10,000) = 15,000 (-3,000).
    # Medical: actual 60,000, limit 10% of 5 lakh = 50,000 (-10,000). Payable 190,000 on 178,000 claimed.
    items = [LineItem("Permanent partial disablement - loss of left thumb", money(100000), "ppd"),
             LineItem("Temporary total disablement - 3 weeks", money(18000), "ttd"),
             LineItem("Accident medical expenses - surgery", money(60000), "medical_expenses")]
    r = adjudicate_benefits(items, money(178000), terms("PA-SECURE"), money(500000), money(500000))
    assert [a for rule, a in steps(r) if rule == "R25_BENEFIT_SCHEDULE"] == [money(25000), money(-3000), money(-10000)]
    assert r.payable == money(190000) and r.non_covered == money(13000)


@pytest.mark.parametrize("description,expected", [("Loss of right index finger", 50000), ("Loss of hearing in one ear", 75000),
                                                   ("Loss of one hand", 250000), ("Crushed knee", 0)])
def test_disablement_schedule_rows(description, expected):
    r = adjudicate_benefits([LineItem(description, money(1), "ppd")], money(1), terms("PA-SECURE"), money(500000), money(500000))
    assert r.payable == money(expected)


def test_benefit_not_in_the_schedule_is_not_covered():
    r = adjudicate_benefits([LineItem("Loss of income", money(40000), "income_loss")], money(40000), terms("PA-SECURE"),
                            money(500000), money(500000))
    assert steps(r)[1] == ("R10_NOT_COVERED", money(-40000)) and r.payable == 0


def test_claim_type_must_match_the_policy_line(client):
    h = login(client, "adjuster")
    r = client.post("/api/v1/claims", headers=h, json={"policy_number": "CS-TRV-26-002101", "claim_type": "health",
                                                       "claimant_name": "Aditi Rao"})
    assert r.status_code == 422 and "travel" in r.text
    lines = {p["policy_number"]: p["line_of_business"] for p in client.get("/api/v1/insured-policies", headers=h).json()}
    assert lines["CS-TRV-26-002101"] == "travel" and set(lines.values()) == {"health", "motor", "travel", "home",
                                                                              "personal_accident", "life"}


@pytest.mark.parametrize("line,recommendation,payable", [("travel", "PARTIAL_APPROVAL", "35800.00"),
                                                         ("home", "PARTIAL_APPROVAL", "74000.00"),
                                                         ("personal_accident", "APPROVE", "190000.00"),
                                                         ("life", "RECOMMEND_REJECT", "0.00")])
def test_sample_packet_for_each_line_runs_through_the_pipeline(client, line, recommendation, payable):
    h = login(client, "supervisor")
    p = client.get(f"/api/v1/demo-packet?line={line}", headers=h).json()
    assert p["claim_type"] == line and len(p["files"]) >= 3
    n = client.post("/api/v1/claims", headers=h, json={k: p[k] for k in ("policy_number", "claim_type", "claimant_name",
                                                                          "description")}).json()["claim_number"]
    files = [("files", (f["name"], client.get(f"/api/v1/demo-packet/{f['name']}?line={line}", headers=h).content,
                        "text/plain")) for f in p["files"]]
    assert client.post(f"/api/v1/claims/{n}/documents", headers=h, files=files).status_code == 201
    assert client.post(f"/api/v1/claims/{n}/analyze", headers=h).json()["status"] == "SUCCEEDED"
    c = client.get(f"/api/v1/claims/{n}", headers=h).json()
    r = client.get(f"/api/v1/claims/{n}/analysis", headers=h).json()["result"]
    assert (c["recommendation"], r["adjudication"]["payable_amount"]) == (recommendation, payable), n


def test_no_sample_packet_for_motor(client):
    assert client.get("/api/v1/demo-packet?line=motor").status_code == 404
    assert client.get("/api/v1/demo-packet?line=marine").status_code == 422


def test_industry_benchmark_is_served_with_its_provenance(client):
    h = login(client, "auditor")
    b = client.get("/api/v1/benchmarks/industry", headers=h).json()
    assert set(b["lines"]) == {"ppauto", "comauto", "wkcomp", "medmal", "othliab", "prodliab"}
    assert b["rows_read"] == 71650 and b["registry"]["valid"] and b["registry"]["status"] == "IN_USE"
    for v in b["lines"].values():
        paid = [d["percent_paid"] for d in v["paid_development"]]
        assert paid == sorted(paid) and paid[-1] == 100.0 and 0.3 < v["loss_ratio"] < 1.5


def test_full_portfolio_covers_six_lines_and_seven_patterns(client):
    a = client.get("/api/v1/analytics", headers=login(client, "auditor")).json()["portfolio_full"]
    assert a["claims"] == 10000 and set(a["by_line"]) == {"health", "motor", "travel", "home", "personal_accident", "life"}
    assert len(a["patterns"]) == 7 and all(a["patterns"][p]["recall"] == 1.0 for p in ("AMOUNT_ANOMALY", "DUPLICATE_CLAIM"))
