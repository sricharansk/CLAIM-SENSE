import json
from decimal import Decimal

from app.adjudication import rules

from .conftest import DATA

HEALTH = json.loads((DATA / "policies" / "HLT-SHIELD_2025.1.terms.json").read_text())
MOTOR = json.loads((DATA / "policies" / "MTR-SECURE_2025.1.terms.json").read_text())
D = Decimal


def items(*rows):
    return [rules.LineItem(desc, D(str(amt)), cat) for desc, amt, cat in rows]


def test_health_waterfall_matches_hand_calculation():
    li = items(("Room Rent - Twin Sharing (3 days @ 6,500)", 19500, "room_rent"), ("Surgeon", 45000, "professional_fees"),
               ("OT", 18000, "ot_charges"), ("Pharmacy", 12500, "medicines"), ("Lab", 8200, "diagnostics"),
               ("Gloves and kit", 3400, "consumables"))
    r = rules.adjudicate_health(li, D("106600"), HEALTH, D("500000"))
    # 106600 - 3400 consumables - (19500 - 3*5000) room excess = 98700; -5000 deductible = 93700; -10% = 84330
    assert r.gross_billed == D("106600.00")
    assert r.non_covered == D("7900.00")
    assert r.deductible == D("5000.00")
    assert r.copay == D("9370.00")
    assert r.payable == D("84330.00")
    assert [s.rule_id for s in r.steps] == ["R00_GROSS", "R20_PER_DAY_LIMIT", "R10_NON_PAYABLE", "R30_DEDUCTIBLE",
                                            "R40_COPAY", "R50_MAX_LIABILITY"]
    assert all(s.clause_ref for s in r.steps[1:])


def test_deductible_never_makes_payable_negative():
    r = rules.adjudicate_health(items(("Consultation", 3000, "professional_fees")), D("3000"), HEALTH, D("500000"))
    assert r.deductible == D("3000.00")
    assert r.payable == D("0.00")


def test_payable_capped_at_available_sum_insured():
    r = rules.adjudicate_health(items(("Surgery", 900000, "professional_fees")), D("900000"), HEALTH, D("300000"))
    assert r.payable == D("300000.00")
    assert r.steps[-1].rule_id == "R50_MAX_LIABILITY" and r.steps[-1].adjustment < 0


def test_copay_rounding_is_half_up_to_paise():
    r = rules.adjudicate_health(items(("Pharmacy", "5000.05", "medicines")), D("5000.05"), HEALTH, D("500000"))
    # (5000.05 - 5000) * 10% = 0.005 -> 0.01
    assert r.copay == D("0.01")
    assert r.payable == D("0.04")


def test_motor_depreciation_by_part_and_vehicle_age():
    li = items(("Rear Bumper", 12000, "parts_plastic"), ("Boot Lid", 26000, "parts_metal"), ("Glass", 9000, "glass"),
               ("Labour", 14000, "labour"), ("Paint", 6000, "paint"))
    r = rules.adjudicate_motor(li, D("67000"), MOTOR, D("650000"), vehicle_age_months=34, engine_cc=1197)
    # 6000 + 3900 (15% metal at 34 months) + 0 + 0 + 3000 = 12900 depreciation; then 2000 deductible
    assert r.depreciation == D("12900.00")
    assert r.deductible == D("2000.00")
    assert r.payable == D("52100.00")


def test_motor_metal_depreciation_bands_and_cc_deductible():
    assert rules.metal_depreciation(MOTOR, 5) == 0
    assert rules.metal_depreciation(MOTOR, 12) == 5
    assert rules.metal_depreciation(MOTOR, 61) == 40
    r = rules.adjudicate_motor(items(("Labour", 10000, "labour")), D("10000"), MOTOR, D("500000"), 10, 1997)
    assert r.deductible == D("3500.00")


def test_not_admissible_zeroes_payable_with_clause():
    r = rules.not_admissible(items(("Surgery", 32000, "professional_fees")), D("32000"), "3.3", "waiting period")
    assert r.payable == D("0.00")
    assert r.steps[-1].clause_ref == "3.3"
