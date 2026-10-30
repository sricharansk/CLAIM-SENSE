"""Personal accident and life: the benefit schedule worked by hand, the accident-only and suicide-window coverage
checks, and the life contestable period in the risk rules."""
import json
from decimal import Decimal

import pytest

from app.adjudication import rules
from app.agents import document as docai
from app.agents.risk import level, score_features

from .conftest import DATA, login

PA = json.loads((DATA / "policies" / "PA-SECURE_2025.1.terms.json").read_text())
LIFE = json.loads((DATA / "policies" / "LIFE-TERM_2025.1.terms.json").read_text())
D = Decimal


def steps(r) -> list[tuple[str, Decimal]]:
    return [(s.rule_id, s.adjustment) for s in r.steps]


def test_personal_accident_pays_the_schedule_not_the_amount_claimed():
    # Thumb: 25% of 5 lakh = 1,25,000 (+25,000). Disablement: 3 weeks x min(1% of 5 lakh, 10,000) = 15,000 (-3,000).
    # Medical: actual 60,000, limit 10% of 5 lakh = 50,000 (-10,000). Payable 1,90,000 on 1,78,000 claimed.
    items = [rules.LineItem("Permanent Partial Disablement - loss of left thumb", D("100000"), "ppd"),
             rules.LineItem("Temporary Total Disablement - 3 weeks", D("18000"), "ttd"),
             rules.LineItem("Accident Medical Expenses - Surgery", D("60000"), "medical_expenses")]
    r = rules.adjudicate_benefits(items, D("178000"), PA, D("500000"), D("500000"))
    assert [a for rule, a in steps(r) if rule == "R20_BENEFIT_SCHEDULE"] == [D("25000.00"), D("-3000.00"), D("-10000.00")]
    assert r.payable == D("190000.00") and r.non_covered == D("13000.00") and r.deductible == 0
    assert all(s.clause_ref for s in r.steps[1:])


def test_weekly_benefit_is_capped_at_10000_a_week():
    # 1% of 12 lakh = 12,000 a week, capped at 10,000: 6 weeks = 60,000
    r = rules.adjudicate_benefits([rules.LineItem("Temporary Total Disablement - 6 weeks", D("72000"), "ttd")],
                                  D("72000"), PA, D("1200000"), D("1200000"))
    assert r.payable == D("60000.00")


@pytest.mark.parametrize("description,expected", [("Loss of right index finger", 50000), ("Loss of hearing in one ear", 75000),
                                                  ("Loss of one hand", 250000), ("Loss of big toe", 25000),
                                                  ("Crushed knee", 0)])
def test_disablement_schedule_rows(description, expected):
    r = rules.adjudicate_benefits([rules.LineItem(description, D("1"), "ppd")], D("1"), PA, D("500000"), D("500000"))
    assert r.payable == D(expected)


def test_benefit_not_in_the_schedule_is_not_payable():
    r = rules.adjudicate_benefits([rules.LineItem("Loss of income", D("40000"), "other")], D("40000"), PA,
                                  D("500000"), D("500000"))
    assert steps(r)[1] == ("R10_NON_PAYABLE", D("-40000.00")) and r.payable == 0


def test_benefits_stop_at_the_available_sum_insured():
    # an earlier approved claim used 3 of the 5 lakh; accidental death is 5 lakh but only 2 lakh is left
    r = rules.adjudicate_benefits([rules.LineItem("Accidental Death Benefit", D("500000"), "accidental_death")],
                                  D("500000"), PA, D("500000"), D("200000"))
    assert ("R50_MAX_LIABILITY", D("-300000.00")) in steps(r) and r.payable == D("200000.00")


def test_life_death_benefit_is_the_sum_assured():
    r = rules.adjudicate_benefits([rules.LineItem("Death Benefit - Sum Assured", D("1500000"), "death_benefit")],
                                  D("1500000"), LIFE, D("1500000"), D("1500000"))
    assert r.payable == D("1500000.00")


@pytest.mark.parametrize("line,description,category", [
    ("personal_accident", "Accidental Death Benefit", "accidental_death"),
    ("personal_accident", "Permanent Total Disablement - paraplegia", "ptd"),
    ("personal_accident", "Accident Medical Expenses - Surgery", "medical_expenses"),
    ("life", "Death Benefit - Sum Assured", "death_benefit")])
def test_benefit_lines_are_categorised_by_the_benefit_claimed(line, description, category):
    assert docai.categorize(description, line)[0] == category


def test_benefit_documents_are_classified():
    assert docai.classify("BENEFIT CLAIM STATEMENT — LIFE") == "claim_statement"
    assert docai.classify("DEATH CERTIFICATE\nDeceased Name: X") == "death_certificate"
    assert docai.classify("MEDICAL ATTENDANT'S CERTIFICATE\nCause of Death: Y") == "medical_certificate"


def test_life_risk_uses_the_contestable_period_not_the_amount_ratio():
    early, _ = score_features({"amount_ratio": 0, "days_since_start": None, "days_in_force": 531, "contestable_days": 1095})
    late, signals = score_features({"amount_ratio": 0, "days_since_start": None, "days_in_force": 1500, "contestable_days": 1095})
    assert level(early) == "HIGH" and level(late) == "LOW" and signals == []


def test_seeded_benefit_claims_reach_their_golden_outcome(client):
    """Accident-only cover (1.3), the alcohol exclusion and the 12-month suicide window, through the full pipeline."""
    h = login(client, "supervisor")
    want = {"CLM-A-5004": ("RECOMMEND_REJECT", "NOT_ACCIDENTAL"), "CLM-A-5005": ("RECOMMEND_REJECT", "EXCL_ALCOHOL"),
            "CLM-L-6003": ("RECOMMEND_REJECT", "EXCL_SUICIDE"), "CLM-L-6004": ("APPROVE", None),
            "CLM-L-6002": ("INVESTIGATE", None)}
    for number, (rec, failing) in want.items():
        res = client.get(f"/api/v1/claims/{number}/analysis", headers=h).json()["result"]
        fail = next((f["code"] for f in res["coverage"]["findings"] if f["outcome"] == "FAIL"), None)
        assert (res["recommendation"]["decision"], fail) == (rec, failing), number
