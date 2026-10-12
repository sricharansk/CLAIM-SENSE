"""Generate the Claim Sense synthetic demo corpus.

Everything produced here is SYNTHETIC: a fictional insurer, fictional people and
fictional policy wording written for this demo. The wording borrows common Indian
retail-insurance concepts (waiting periods, co-pay, room-rent limits, depreciation)
but it is not any insurer's product and not regulatory text.

Outputs (deterministic, seed=2025):
  data/policies/<product>_<version>.md          policy wording with page/section/clause markers
  data/policies/<product>_<version>.terms.json  structured terms, each pointing at its clause
  data/policies/insured_policies.json           customer policy contracts
  data/claims/<CLAIM>/*.txt|pdf                 claim document packets for the golden scenarios
  data/claims/scenarios.json                    claim headers + expected outcome
  data/evaluation/packets/<CASE>/*.txt          extra packets used only by scripts/evaluate.py (never seeded)
  data/policies/ingest_demo/HLT-SHIELD_2026.1.pdf  a new wording version as a multi-page PDF, for live ingestion
  data/synthetic/claims_portfolio.csv           1,000 claims with injected fraud patterns

Run: python data/synthetic/generate.py
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POL = ROOT / "data" / "policies"
CLM = ROOT / "data" / "claims"
SYN = ROOT / "data" / "synthetic"
EVAL = ROOT / "data" / "evaluation" / "packets"
INSURER = "Synthetic Assurance Co. Ltd. (fictional)"
NOTICE = ("This is SYNTHETIC policy wording created for the Claim Sense demo. It is not issued by any "
          "real insurer and is not regulatory text.")

# ---------------------------------------------------------------- health ---
HEALTH_VERSIONS = {
    "2024.1": dict(effective_from="2024-04-01", effective_to="2025-03-31", room=4000, icu=8000,
                   deductible=10000, copay=20, ped_months=48, notify_hours=24),
    "2025.1": dict(effective_from="2025-04-01", effective_to="2026-03-31", room=5000, icu=10000,
                   deductible=5000, copay=10, ped_months=36, notify_hours=48),
}
# Not seeded: ingested live through the Policy library to demonstrate PDF ingestion.
DEMO_INGEST_VERSION = ("2026.1", dict(effective_from="2026-04-01", effective_to="2027-03-31", room=6000, icu=12000,
                                      deductible=5000, copay=10, ped_months=36, notify_hours=48))
SPECIFIED = ["cataract", "hernia", "joint replacement", "kidney stone", "sinusitis", "tonsillectomy", "varicose veins"]


def inr(n: int) -> str:
    return f"INR {n:,}"


def health_wording(v: str, p: dict) -> str:
    return f"""# ClaimSense Health Shield — Policy Wording (Version {v})

<!-- page: 1 -->
## 1. Preamble and Definitions

### 1.1 Insurer and Policy
This policy is issued by {INSURER}. Product code HLT-SHIELD, wording version {v}, effective for policies and renewals incepting from {p['effective_from']} to {p['effective_to']}. {NOTICE}

### 1.2 Hospitalisation
Hospitalisation means admission in a hospital for a minimum period of 24 consecutive in-patient care hours, except for day care procedures listed in the annexure.

### 1.3 Sum Insured
Sum insured means the maximum amount stated in the policy schedule that the insurer will pay for all claims admitted during the policy year.

<!-- page: 2 -->
## 2. Coverage

### 2.1 In-patient Hospitalisation Expenses
The insurer will indemnify medically necessary expenses incurred for in-patient hospitalisation during the policy period, including room and boarding, nursing, intensive care, surgeon and consultant fees, operation theatre charges, medicines and drugs, and diagnostic tests, subject to the limits, waiting periods, exclusions and cost-sharing in this policy.

### 2.2 Room Rent Limit
Room rent, boarding and nursing charges are payable up to {inr(p['room'])} per day of hospitalisation. Any room rent charged above {inr(p['room'])} per day is not payable.

### 2.3 Intensive Care Unit Limit
Intensive care unit charges are payable up to {inr(p['icu'])} per day of stay in the intensive care unit. Charges above this limit are not payable.

### 2.4 Pre and Post Hospitalisation
Medical expenses incurred up to 30 days before admission and up to 60 days after discharge for the same condition are payable, provided the in-patient claim is admissible.

<!-- page: 3 -->
## 3. Waiting Periods

### 3.1 Initial Waiting Period
Expenses for any illness contracted within the first 30 days from the first policy commencement date are not payable. This initial waiting period does not apply to hospitalisation caused by an accident.

### 3.2 Pre-existing Diseases
Expenses related to a pre-existing disease declared or detected at proposal are payable only after {p['ped_months']} months of continuous coverage from the first policy commencement date.

### 3.3 Specified Diseases and Procedures
Treatment of the following is payable only after 24 months of continuous coverage: {", ".join(SPECIFIED)}. This waiting period does not apply when treatment is required because of an accident.

<!-- page: 4 -->
## 4. Exclusions

### 4.1 Cosmetic and Aesthetic Treatment
Cosmetic, aesthetic or plastic surgery, including weight reduction and hair transplant, is not payable unless required to treat an injury caused by an accident.

### 4.2 Alcohol, Substance Abuse and Self-inflicted Injury
Treatment arising from alcohol or drug abuse, intoxication, or intentional self-inflicted injury is not payable.

### 4.3 Non-medical Items and Consumables
Non-medical items and consumables such as gloves, masks, admission kits, registration and file charges, toiletries and attendant charges are not payable.

### 4.4 Maternity
Expenses for childbirth, caesarean section and pregnancy-related treatment are not payable under this policy.

### 4.5 Unproven and Experimental Treatment
Treatment that is experimental, investigational or not based on established medical practice is not payable.

<!-- page: 5 -->
## 5. Cost Sharing

### 5.1 Deductible
A deductible of {inr(p['deductible'])} applies to each admissible hospitalisation claim. The deductible is subtracted from the admissible amount before co-payment.

### 5.2 Co-payment
A co-payment of {p['copay']}% of the admissible amount remaining after the deductible is borne by the insured on every claim.

### 5.3 Maximum Liability
The total amount payable for all claims in a policy year will not exceed the available sum insured.

<!-- page: 6 -->
## 6. Claims Procedure

### 6.1 Claim Notification
The insured must notify the insurer within {p['notify_hours']} hours of an emergency admission and at least 48 hours before a planned admission.

### 6.2 Documents Required
A hospitalisation claim must include the duly filled claim form, the discharge summary, the final hospital bill with itemised breakup, and payment receipts. The insurer may request investigation reports where needed.

### 6.3 Claim Settlement
The insurer will settle or reject a claim within 30 days of receiving the last necessary document. Any rejection will be communicated in writing with the specific policy clause relied upon.
"""


def health_terms(v: str, p: dict) -> dict:
    return {
        "product_code": "HLT-SHIELD", "product_name": "ClaimSense Health Shield", "line_of_business": "health",
        "insurer": INSURER, "version": v, "effective_from": p["effective_from"], "effective_to": p["effective_to"],
        "limits": {
            "room_rent_per_day": {"amount": p["room"], "clause": "2.2"},
            "icu_per_day": {"amount": p["icu"], "clause": "2.3"},
        },
        "deductible": {"amount": p["deductible"], "clause": "5.1"},
        "copay_percent": {"value": p["copay"], "clause": "5.2"},
        "max_liability_clause": "5.3",
        "waiting_periods": {
            "initial_days": {"value": 30, "clause": "3.1", "accident_exempt": True},
            "specified_months": {"value": 24, "clause": "3.3", "conditions": SPECIFIED, "accident_exempt": True},
            "ped_months": {"value": p["ped_months"], "clause": "3.2"},
        },
        "exclusions": [
            {"code": "EXCL_COSMETIC", "clause": "4.1", "keywords": ["cosmetic", "aesthetic", "hair transplant", "liposuction", "weight reduction"]},
            {"code": "EXCL_ALCOHOL", "clause": "4.2", "keywords": ["alcohol", "intoxication", "drunk", "substance abuse", "self-inflicted", "overdose"]},
            {"code": "EXCL_MATERNITY", "clause": "4.4", "keywords": ["maternity", "childbirth", "caesarean", "delivery", "pregnancy"]},
            {"code": "EXCL_EXPERIMENTAL", "clause": "4.5", "keywords": ["experimental", "investigational"]},
        ],
        "non_payable_categories": {"consumables": "4.3", "non_medical": "4.3"},
        "category_limits": {"room_rent": "room_rent_per_day", "icu": "icu_per_day"},
        "required_documents": {"documents": ["claim_form", "discharge_summary", "hospital_bill"], "clause": "6.2"},
        "settlement_days": {"value": 30, "clause": "6.3"},
        "coverage_clause": "2.1",
    }


# ----------------------------------------------------------------- motor ---
def motor_wording() -> str:
    return f"""# ClaimSense Motor Secure — Private Car Package Policy Wording (Version 2025.1)

<!-- page: 1 -->
## 1. Preamble and Definitions

### 1.1 Insurer and Policy
This policy is issued by {INSURER}. Product code MTR-SECURE, wording version 2025.1, effective for policies incepting from 2025-04-01 to 2026-03-31. {NOTICE}

### 1.2 Insured Declared Value
The insured declared value (IDV) is the sum insured for the vehicle stated in the schedule. The insurer's liability for own damage in any one claim shall not exceed the IDV.

<!-- page: 2 -->
## 2. Own Damage Cover

### 2.1 Loss or Damage to the Vehicle
The insurer will indemnify the insured against accidental loss of or damage to the insured vehicle caused by collision, overturning, fire, theft, flood, storm or malicious act, by repairing the vehicle or paying for the reasonable cost of repair.

### 2.2 Depreciation on Parts
Depreciation is deducted from the cost of parts replaced: 50% on rubber, nylon and plastic parts; 30% on fibre glass parts; nil on glass parts. Depreciation on metal parts depends on the age of the vehicle: nil up to 6 months, 5% up to 1 year, 10% up to 2 years, 15% up to 3 years, 25% up to 4 years, 35% up to 5 years and 40% beyond 5 years. Painting material attracts 50% depreciation. Labour charges are payable without depreciation.

### 2.3 Compulsory Deductible
A compulsory deductible of INR 2,000 applies to each own damage claim for private cars up to 1500cc and INR 3,500 above 1500cc.

<!-- page: 3 -->
## 3. Exclusions

### 3.1 Driving Under the Influence
No claim is payable for loss or damage sustained while the vehicle is driven by a person under the influence of alcohol or drugs.

### 3.2 Driver Without a Valid Licence
No claim is payable when the vehicle is driven by a person who does not hold a valid and effective driving licence.

### 3.3 Wear, Tear and Mechanical Breakdown
Normal wear and tear, depreciation, mechanical or electrical breakdown and consequential loss are not payable.

### 3.4 Use Outside Geographical Area
Loss or damage arising while the vehicle is used outside India is not payable.

<!-- page: 4 -->
## 4. Claims Procedure

### 4.1 Claim Intimation
The insured must intimate the insurer immediately and in any case within 7 days of the accident. A police report (FIR) is required for theft, third-party injury or malicious damage.

### 4.2 Documents Required
An own damage claim must include the claim form, the repair estimate from the workshop, a copy of the driving licence and the registration certificate. Photographs of the damage should be submitted where available.

### 4.3 Claim Settlement
The insurer will settle the claim within 30 days of receiving the survey report and all necessary documents.
"""


def motor_terms() -> dict:
    return {
        "product_code": "MTR-SECURE", "product_name": "ClaimSense Motor Secure", "line_of_business": "motor",
        "insurer": INSURER, "version": "2025.1", "effective_from": "2025-04-01", "effective_to": "2026-03-31",
        "deductible": {"amount": 2000, "amount_above_1500cc": 3500, "clause": "2.3"},
        "depreciation": {
            "clause": "2.2",
            "flat_percent": {"parts_plastic": 50, "parts_fibre": 30, "glass": 0, "paint": 50, "labour": 0},
            "metal_by_age_months": [[6, 0], [12, 5], [24, 10], [36, 15], [48, 25], [60, 35], [100000, 40]],
        },
        "max_liability_clause": "1.2",
        "exclusions": [
            {"code": "EXCL_DUI", "clause": "3.1", "keywords": ["under the influence", "breath analyser test positive", "drunk", "intoxicated", "alcohol"]},
            {"code": "EXCL_NO_LICENCE", "clause": "3.2", "keywords": ["no valid licence", "licence expired", "unlicensed"]},
            {"code": "EXCL_WEAR_TEAR", "clause": "3.3", "keywords": ["wear and tear", "mechanical breakdown", "electrical breakdown"]},
            {"code": "EXCL_OUTSIDE_INDIA", "clause": "3.4", "keywords": ["outside india", "nepal", "bhutan"]},
        ],
        "non_payable_categories": {},
        "required_documents": {"documents": ["claim_form", "repair_estimate", "driving_licence"], "clause": "4.2"},
        "settlement_days": {"value": 30, "clause": "4.3"},
        "coverage_clause": "2.1",
    }



# -------------------------------------------------------------- property ---
def property_wording() -> str:
    return f"""# ClaimSense Home Guard — Householder's Package Policy Wording (Version 2025.1)

<!-- page: 1 -->
## 1. Preamble and Definitions

### 1.1 Insurer and Policy
This policy is issued by {INSURER}. Product code HOME-GUARD, wording version 2025.1, effective for policies incepting from 2024-04-01 to 2026-03-31. {NOTICE}

### 1.2 Sum Insured
The sum insured is the amount stated in the schedule for the building and its contents together. The insurer's liability in any one claim shall not exceed the sum insured.

### 1.3 Value at Risk
Value at risk means the full cost of rebuilding the building and of replacing the contents as new at the time of loss, as declared in the claim form and verified by the surveyor.

<!-- page: 2 -->
## 2. Coverage

### 2.1 Insured Perils
The insurer will indemnify sudden and accidental physical loss of or damage to the insured building and contents caused by fire, lightning, explosion, storm, cyclone, flood, inundation, earthquake, bursting or overflowing of water tanks and pipes, and burglary or housebreaking involving forcible entry.

### 2.2 Depreciation on Contents
Contents are indemnified at replacement cost less depreciation: 20% on electronic and electrical appliances and 10% on furniture and furnishings. Repairs to the building are payable without depreciation.

### 2.3 Underinsurance (Average Clause)
If the value at risk at the time of loss exceeds the sum insured by more than 15%, the insured shall be considered their own insurer for the difference, and the assessed loss shall be reduced in the proportion that the sum insured bears to the value at risk.

<!-- page: 3 -->
## 3. Exclusions

### 3.1 Gradual Deterioration
Loss or damage caused by wear and tear, gradual deterioration, seepage, dampness, leakage over a period of time, termites or vermin is not payable.

### 3.2 Wilful Act
Loss or damage caused by a wilful, intentional or fraudulent act of the insured or a member of the household is not payable.

### 3.3 Unoccupied Premises
Loss or damage occurring while the premises have been unoccupied for more than 60 consecutive days is not payable unless the insurer has agreed in writing.

### 3.4 War and Nuclear Risks
Loss or damage caused by an act of war, invasion, nuclear reaction or radioactive contamination is not payable.

### 3.5 Valuables Not Covered
Jewellery, gold, bullion, cash, cheques and documents are not covered unless specifically listed in the schedule with a separate sum insured.

<!-- page: 4 -->
## 4. Cost Sharing

### 4.1 Excess
An excess of INR 10,000 applies to each claim and is borne by the insured.

<!-- page: 5 -->
## 5. Claims Procedure

### 5.1 Claim Intimation
The insured must notify the insurer within 7 days of the loss. Burglary, theft and malicious damage must also be reported to the police immediately.

### 5.2 Documents Required
A claim must include the claim form and the surveyor's loss assessment with an itemised breakup of the loss. A police report (FIR) is also required for burglary, housebreaking, theft or malicious damage.

### 5.3 Claim Settlement
The insurer will settle or reject the claim within 30 days of receiving the surveyor's final report and all necessary documents.
"""


def property_terms() -> dict:
    return {
        "product_code": "HOME-GUARD", "product_name": "ClaimSense Home Guard", "line_of_business": "property",
        "insurer": INSURER, "version": "2025.1", "effective_from": "2024-04-01", "effective_to": "2026-03-31",
        "deductible": {"amount": 10000, "clause": "4.1"},
        "depreciation": {"clause": "2.2", "flat_percent": {"contents_electronics": 20, "contents_furniture": 10}},
        "underinsurance": {"clause": "2.3", "tolerance_percent": 15},
        "max_liability_clause": "1.2",
        "exclusions": [
            {"code": "EXCL_GRADUAL_DETERIORATION", "clause": "3.1",
             "keywords": ["gradual deterioration", "wear and tear", "seepage", "dampness", "termite", "vermin"]},
            {"code": "EXCL_WILFUL_ACT", "clause": "3.2", "keywords": ["wilful", "intentional", "deliberately set"]},
            {"code": "EXCL_UNOCCUPIED", "clause": "3.3", "keywords": ["unoccupied", "lying vacant"]},
            {"code": "EXCL_WAR_NUCLEAR", "clause": "3.4", "keywords": ["act of war", "invasion", "nuclear", "radioactive"]},
        ],
        "non_payable_categories": {"valuables": "3.5"},
        "required_documents": {"documents": ["claim_form", "loss_assessment"], "clause": "5.2"},
        "conditional_documents": [{"document": "police_report", "keywords": ["burglary", "housebreaking", "theft", "stolen"]}],
        "settlement_days": {"value": 30, "clause": "5.3"},
        "coverage_clause": "2.1",
    }


# ---------------------------------------------------------------- travel ---
def travel_wording() -> str:
    return f"""# ClaimSense Travel Globe — Overseas Travel Insurance Policy Wording (Version 2025.1)

<!-- page: 1 -->
## 1. Preamble and Definitions

### 1.1 Insurer and Policy
This policy is issued by {INSURER}. Product code TRV-GLOBE, wording version 2025.1, effective for policies incepting from 2025-04-01 to 2026-03-31. {NOTICE}

### 1.2 Sum Insured
The sum insured is the amount stated in the schedule. The insurer's liability for all claims arising from one trip shall not exceed the sum insured.

### 1.3 Period of Cover
Cover for a trip operates from the departure date to the return date stated in the schedule or claim form. An event before the departure date or after the return date is not covered.

### 1.4 Currency
Claims are assessed and paid in Indian rupees. Expenses incurred in a foreign currency are converted at the reference rate on the date of loss, as shown in the expense statement.

<!-- page: 2 -->
## 2. Benefits

### 2.1 Emergency Medical Expenses
The insurer will pay reasonable and customary charges for emergency medical treatment of a sudden illness or accidental injury during the trip, including hospital room, physician and surgeon fees, medicines, diagnostic tests and emergency ambulance.

### 2.2 Trip Cancellation and Interruption
The insurer will reimburse non-refundable airfare, hotel and tour package costs when the trip is cancelled or cut short because of serious illness, injury or death of the insured or an immediate family member, a natural disaster, or closure of an airport by the authorities, up to INR 1,50,000 per trip.

### 2.3 Checked Baggage Loss
The insurer will pay for checked baggage permanently lost by the airline up to INR 1,00,000 per trip, subject to a maximum of INR 25,000 for any one item, pair or set. A property irregularity report from the airline is required.

### 2.4 Non-payable Items
Personal comfort items such as toiletries, telephone calls and laundry during treatment are not payable.

<!-- page: 3 -->
## 3. Exclusions

### 3.1 Pre-existing Conditions
Treatment of a pre-existing condition, or of any condition for which the insured was under treatment before departure, is not covered.

### 3.2 Hazardous Sports
Injury sustained while taking part in paragliding, skydiving, bungee jumping, scuba diving, mountaineering or motor racing is not covered.

### 3.3 Alcohol and Drugs
Any claim arising while the insured is under the influence of alcohol or drugs not prescribed by a doctor is not covered.

### 3.4 Travel Against Medical Advice
Any claim arising from a trip undertaken against medical advice or for the purpose of obtaining medical treatment is not covered.

<!-- page: 4 -->
## 4. Cost Sharing

### 4.1 Deductible
A deductible of INR 5,000 applies to each claim and is borne by the insured.

<!-- page: 5 -->
## 5. Claims Procedure

### 5.1 Claim Intimation
The insured must notify the assistance service within 48 hours of a hospital admission and the insurer within 30 days of returning to India.

### 5.2 Documents Required
A claim must include the claim form, an itemised expense statement with invoices, and proof of travel such as boarding passes or passport stamps. A medical report from the treating doctor is required for medical claims, and a property irregularity report from the airline for baggage claims.

### 5.3 Claim Settlement
The insurer will settle or reject the claim within 30 days of receiving all necessary documents.
"""


def travel_terms() -> dict:
    return {
        "product_code": "TRV-GLOBE", "product_name": "ClaimSense Travel Globe", "line_of_business": "travel",
        "insurer": INSURER, "version": "2025.1", "effective_from": "2025-04-01", "effective_to": "2026-03-31",
        "trip_based": True, "trip_period_clause": "1.3",
        "deductible": {"amount": 5000, "clause": "4.1"},
        "benefit_limits": {
            "trip_cancellation": {"amount": 150000, "clause": "2.2", "categories": ["trip_cancellation"]},
            "checked_baggage": {"amount": 100000, "per_item": 25000, "clause": "2.3", "categories": ["baggage_item"]},
        },
        "max_liability_clause": "1.2",
        "exclusions": [
            {"code": "EXCL_PRE_EXISTING", "clause": "3.1", "keywords": ["pre-existing", "under treatment before departure"]},
            {"code": "EXCL_HAZARDOUS_SPORTS", "clause": "3.2",
             "keywords": ["paragliding", "skydiving", "bungee", "scuba", "mountaineering", "motor racing"]},
            {"code": "EXCL_ALCOHOL", "clause": "3.3", "keywords": ["alcohol", "intoxicated", "drunk"]},
            {"code": "EXCL_AGAINST_ADVICE", "clause": "3.4", "keywords": ["against medical advice", "travelled for treatment"]},
        ],
        "non_payable_categories": {"personal_comfort": "2.4"},
        "required_documents": {"documents": ["claim_form", "expense_statement", "travel_proof"], "clause": "5.2"},
        "conditional_documents": [
            {"document": "medical_report", "keywords": ["hospital", "admitted", "surgery", "operated"]},
            {"document": "property_irregularity_report", "keywords": ["baggage", "suitcase"]},
        ],
        "settlement_days": {"value": 30, "clause": "5.3"},
        "coverage_clause": "2.1",
    }


INSURED = [
    # policy_number, product, holder, start, end, sum insured
    ("CS-HLT-24-000117", "HLT-SHIELD", "Ravi Kumar", "2024-06-01", "2026-05-31", 500000),
    ("CS-HLT-25-000342", "HLT-SHIELD", "Meena Iyer", "2025-02-10", "2026-02-09", 300000),
    ("CS-HLT-25-000518", "HLT-SHIELD", "Arjun Mehta", "2025-05-01", "2026-04-30", 500000),
    ("CS-HLT-23-000089", "HLT-SHIELD", "Fatima Shaikh", "2023-09-15", "2026-09-14", 400000),
    ("CS-HLT-24-000233", "HLT-SHIELD", "Suresh Nair", "2024-01-20", "2026-01-19", 300000),
    ("CS-MTR-25-001204", "MTR-SECURE", "Priya Sharma", "2025-04-15", "2026-04-14", 650000),
    ("CS-MTR-25-001377", "MTR-SECURE", "Karthik Rao", "2025-06-01", "2026-05-31", 480000),
    ("CS-HOM-25-003101", "HOME-GUARD", "Anita Desai", "2025-01-10", "2026-01-09", 2500000),
    ("CS-HOM-24-003145", "HOME-GUARD", "Vikram Singh", "2024-11-01", "2025-10-31", 1200000),
    ("CS-HOM-24-002877", "HOME-GUARD", "Lakshmi Menon", "2024-07-01", "2026-06-30", 1800000),
    ("CS-TRV-25-004410", "TRV-GLOBE", "Rahul Verma", "2025-09-01", "2025-09-20", 4000000),
    ("CS-TRV-25-004468", "TRV-GLOBE", "Neha Kapoor", "2025-04-01", "2026-03-31", 4000000),
    ("CS-TRV-25-004502", "TRV-GLOBE", "Aditya Joshi", "2025-08-10", "2025-08-24", 4000000),
    ("CS-TRV-25-004533", "TRV-GLOBE", "Sana Qureshi", "2025-11-02", "2025-11-12", 4000000),
    ("CS-TRV-25-004588", "TRV-GLOBE", "Kavya Reddy", "2025-06-01", "2026-05-31", 4000000),
    ("CS-HLT-24-000611", "HLT-SHIELD", "Divya Pillai", "2024-03-01", "2026-02-28", 500000),
    ("CS-MTR-25-001452", "MTR-SECURE", "Rohan Gupta", "2025-05-10", "2026-05-09", 520000),
    ("CS-HOM-25-003260", "HOME-GUARD", "Farhan Ali", "2025-02-01", "2026-01-31", 1500000),
    ("CS-TRV-25-004611", "TRV-GLOBE", "Gopal Krishnan", "2025-12-01", "2025-12-15", 4000000),
]


# --------------------------------------------------------------- claims ---
def claim_form(c: dict) -> str:
    lines = ["CLAIM FORM — Synthetic Assurance Co. Ltd. (fictional)", "SYNTHETIC DEMO DOCUMENT", "",
             f"Claim Type: {c['claim_type'].title()}", f"Policy Number: {c['policy_number']}",
             f"Claimant Name: {c['claimant']}", f"Incident Date: {c['incident_date']}"]
    for k, v in c.get("form_extra", {}).items():
        lines.append(f"{k}: {v}")
    lines += [f"Claimed Amount: INR {c['form_amount']:,.2f}", "", "Description of Loss:", c["narrative"], "",
              "I declare that the information given is true and complete.", f"Signed: {c['claimant']}"]
    return "\n".join(lines) + "\n"


def bill(title: str, c: dict, items: list[tuple[str, int]], header: dict) -> str:
    lines = [title, "SYNTHETIC DEMO DOCUMENT", ""] + [f"{k}: {v}" for k, v in header.items()]
    lines += [f"Patient/Insured Name: {c['claimant']}", "", "Itemised Charges:"]
    for desc, amt in items:
        lines.append(f"{desc:<60} {amt:>12,.2f}")
    lines += ["", f"{'Total Amount':<60} {sum(a for _, a in items):>12,.2f}"]
    return "\n".join(lines) + "\n"


def discharge(c: dict, admit: str, disch: str, diagnosis: str, procedure: str, notes: str) -> str:
    return "\n".join([
        "DISCHARGE SUMMARY", "SYNTHETIC DEMO DOCUMENT", "",
        f"Hospital: {c['hospital']}", f"Patient Name: {c['claimant']}", f"Admission Date: {admit}",
        f"Discharge Date: {disch}", f"Diagnosis: {diagnosis}", f"Procedure: {procedure}", "",
        "Clinical Notes:", notes,
    ]) + "\n"


def police_report(c: dict, text: str) -> str:
    return "\n".join(["POLICE / ACCIDENT REPORT", "SYNTHETIC DEMO DOCUMENT", "",
                      f"FIR Number: {c['fir']}", f"Date of Accident: {c['incident_date']}",
                      f"Vehicle Registration: {c['form_extra']['Vehicle Registration']}", "", "Findings:", text]) + "\n"


def licence(c: dict) -> str:
    return "\n".join(["DRIVING LICENCE (COPY)", "SYNTHETIC DEMO DOCUMENT", "",
                      f"Name: {c['claimant']}", "Licence Number: KA01-2016-00SYN" + str(c['claim_number'][-2:]),
                      f"Valid Till: {c.get('licence_valid_till', '2036-03-31')}", "Class: LMV"]) + "\n"


def loss_assessment(c: dict) -> str:
    body = bill("SURVEYOR'S LOSS ASSESSMENT REPORT", c, c["items"],
                {"Surveyor": "Deccan Loss Surveyors (fictional)", "Survey Reference": f"SV-{c['claim_number'][-4:]}",
                 "Incident Date": c["incident_date"]})
    return body + "\nSurveyor Observations:\n" + c["survey"] + "\n"


def property_police_report(c: dict) -> str:
    return "\n".join(["POLICE REPORT (FIR COPY)", "SYNTHETIC DEMO DOCUMENT", "", f"FIR Number: {c['fir']}",
                      f"Incident Date: {c['incident_date']}", "", "Findings:", c["police"]]) + "\n"


def expense_statement(c: dict) -> str:
    return bill("CLAIM EXPENSE STATEMENT", c, c["items"],
                {"Destination": c["form_extra"]["Destination"],
                 "Currency": "Amounts in INR, converted at the reference rate on the date of loss"})


def medical_report(c: dict) -> str:
    m = c["medical"]
    return "\n".join(["MEDICAL REPORT FROM TREATING DOCTOR", "SYNTHETIC DEMO DOCUMENT", "", f"Hospital: {m['hospital']}",
                      f"Patient Name: {c['claimant']}", f"Admission Date: {m['admit']}", f"Discharge Date: {m['disch']}",
                      f"Diagnosis: {m['diagnosis']}", f"Procedure: {m['procedure']}", "", "Clinical Notes:", m["notes"]]) + "\n"


def irregularity_report(c: dict) -> str:
    return "\n".join(["PROPERTY IRREGULARITY REPORT (AIRLINE)", "SYNTHETIC DEMO DOCUMENT", "",
                      f"PIR Reference: {c['pir_ref']}", f"Name: {c['claimant']}", "", "Remarks:", c["pir"]]) + "\n"


def travel_proof(c: dict) -> str:
    f = c["form_extra"]
    return "\n".join(["PROOF OF TRAVEL - BOARDING PASSES AND PASSPORT STAMPS", "SYNTHETIC DEMO DOCUMENT", "",
                      f"Name: {c['claimant']}", f"Destination: {f['Destination']}", f"Departure Date: {f['Departure Date']}",
                      f"Return Date: {f['Return Date']}"]) + "\n"


def line_documents(c: dict) -> dict[str, str]:
    """Documents for the property and travel lines; health and motor packets are built in write_claim_packets."""
    files = {"claim_form.txt": claim_form(c)}
    if c["claim_type"] == "property":
        files["loss_assessment.txt"] = loss_assessment(c)
        if c.get("police"):
            files["police_report.txt"] = property_police_report(c)
    else:
        files["expense_statement.txt"] = expense_statement(c)
        files["travel_proof.txt"] = travel_proof(c)
        if c.get("medical"):
            files["medical_report.txt"] = medical_report(c)
        if c.get("pir"):
            files["property_irregularity_report.txt"] = irregularity_report(c)
    return files


def golden_claims() -> list[dict]:
    S = []
    hosp_items = [("Room Rent - Twin Sharing (3 days @ 6,500)", 19500), ("Surgeon and Anaesthetist Fees", 45000),
                  ("Operation Theatre Charges", 18000), ("Pharmacy - Medicines and Drugs", 12500),
                  ("Laboratory and Diagnostic Tests (CT Abdomen, Blood)", 8200), ("Consumables - Gloves, Masks, Admission Kit", 3400)]
    S.append(dict(claim_number="CLM-H-1001", claim_type="health", policy_number="CS-HLT-24-000117", claimant="Ravi Kumar",
                  incident_date="2025-08-12", hospital="Lakeview Multispeciality Hospital (fictional)",
                  narrative="Sudden severe abdominal pain; admitted through emergency and operated for acute appendicitis.",
                  items=hosp_items, admit="2025-08-12", disch="2025-08-15", diagnosis="Acute appendicitis",
                  procedure="Laparoscopic appendicectomy", notes="Uneventful recovery. Discharged in stable condition.",
                  expected="PARTIAL_APPROVAL", story="Covered surgery with room-rent cap, consumables exclusion, deductible and co-pay"))
    S.append(dict(claim_number="CLM-H-1002", claim_type="health", policy_number="CS-HLT-25-000342", claimant="Meena Iyer",
                  incident_date="2025-09-05", hospital="Clearsight Eye Institute (fictional)",
                  narrative="Planned surgery for progressive blurring of vision in the left eye.",
                  items=[("Room Rent - Day Care (1 day @ 3,000)", 3000), ("Surgeon Fees - Phacoemulsification", 32000),
                         ("Intraocular Lens and Medicines", 24000), ("Diagnostic Tests - Biometry", 2500)],
                  admit="2025-09-05", disch="2025-09-05", diagnosis="Senile cataract, left eye",
                  procedure="Cataract surgery with IOL implant", notes="Planned day care procedure.",
                  expected="RECOMMEND_REJECT", story="Cataract inside the 24-month specified-disease waiting period"))
    S.append(dict(claim_number="CLM-H-1003", claim_type="health", policy_number="CS-HLT-25-000518", claimant="Arjun Mehta",
                  incident_date="2025-06-20", hospital="Sunrise Care Hospital (fictional)",
                  narrative="High fever and breathlessness; admitted to ICU with pneumonia.", form_amount=468000,
                  items=[("ICU Charges (6 days @ 18,000)", 108000), ("Room Rent - Private (5 days @ 9,000)", 45000),
                         ("Consultant and Intensivist Fees", 96000), ("Pharmacy - Medicines and Drugs", 118000),
                         ("Laboratory and Diagnostic Tests", 54000), ("Ventilator and Equipment Charges", 21000)],
                  admit="2025-06-20", disch="2025-07-01", diagnosis="Community acquired pneumonia",
                  procedure="Medical management, non-invasive ventilation", notes="Recovered. Discharged on oral antibiotics.",
                  expected="INVESTIGATE", story="Early claim, 94% of sum insured, claim form amount differs from the bill total"))
    S.append(dict(claim_number="CLM-H-1004", claim_type="health", policy_number="CS-HLT-23-000089", claimant="Fatima Shaikh",
                  incident_date="2025-10-02", hospital="Greenfield General Hospital (fictional)",
                  narrative="Admitted for dengue fever with low platelet count.", skip_discharge=True,
                  items=[("Room Rent - General Ward (4 days @ 3,500)", 14000), ("Consultant Fees", 12000),
                         ("Pharmacy - Medicines and Drugs", 9800), ("Laboratory Tests - Platelet Count Series", 7600)],
                  admit="2025-10-02", disch="2025-10-06", diagnosis="Dengue fever", procedure="Medical management",
                  notes="", expected="REQUEST_INFO", story="Discharge summary missing"))
    S.append(dict(claim_number="CLM-H-1005", claim_type="health", policy_number="CS-HLT-24-000233", claimant="Suresh Nair",
                  incident_date="2025-02-14", hospital="Lakeview Multispeciality Hospital (fictional)",
                  narrative="Fracture of right forearm after a fall at home.",
                  items=[("Room Rent - Twin Sharing (2 days @ 5,500)", 11000), ("Orthopaedic Surgeon Fees", 28000),
                         ("Operation Theatre Charges", 12000), ("Implants and Medicines", 22000), ("X-Ray and Diagnostics", 3500)],
                  admit="2025-02-14", disch="2025-02-16", diagnosis="Distal radius fracture following accidental fall",
                  procedure="Open reduction and internal fixation", notes="Accidental injury.",
                  expected="PARTIAL_APPROVAL", story="Incident before 2025-04-01, so the 2024.1 wording applies"))
    S.append(dict(claim_number="CLM-H-1006", claim_type="health", policy_number="CS-HLT-24-000117", claimant="Ravi Kumar",
                  incident_date="2025-08-12", hospital="Lakeview Multispeciality Hospital (fictional)",
                  narrative="Claim for hospitalisation for appendicitis.", items=hosp_items, admit="2025-08-12",
                  disch="2025-08-15", diagnosis="Acute appendicitis", procedure="Laparoscopic appendicectomy",
                  notes="Uneventful recovery.", expected="INVESTIGATE", story="Duplicate of CLM-H-1001"))
    S.append(dict(claim_number="CLM-M-2001", claim_type="motor", policy_number="CS-MTR-25-001204", claimant="Priya Sharma",
                  incident_date="2025-09-18", fir="FIR-SYN-0918-22",
                  form_extra={"Vehicle Registration": "KA-05-SY-4821", "Vehicle Make and Model": "Hatchback 1197cc",
                              "Date of First Registration": "2022-11-10", "Engine Capacity cc": "1197"},
                  narrative="Rear-ended at a traffic signal on Outer Ring Road; rear bumper, boot lid and tail lamp damaged.",
                  items=[("Rear Bumper (plastic) - replace", 12000), ("Boot Lid Panel (metal) - replace", 26000),
                         ("Tail Lamp Assembly (plastic)", 6500), ("Rear Windshield Glass", 9000),
                         ("Denting and Fitting Labour", 14000), ("Painting Material", 6000)],
                  expected="PARTIAL_APPROVAL", story="Depreciation by part type and vehicle age, plus compulsory deductible"))
    S.append(dict(claim_number="CLM-M-2002", claim_type="motor", policy_number="CS-MTR-25-001377", claimant="Karthik Rao",
                  incident_date="2025-07-27", fir="FIR-SYN-0727-09",
                  form_extra={"Vehicle Registration": "KA-03-SY-1190", "Vehicle Make and Model": "Sedan 1497cc",
                              "Date of First Registration": "2021-03-02", "Engine Capacity cc": "1497"},
                  narrative="Vehicle hit the road divider late at night; front bumper and bonnet damaged.",
                  police="Driver was examined at the spot. Breath analyser test positive; driver found to be under the influence of alcohol.",
                  items=[("Front Bumper (plastic) - replace", 14500), ("Bonnet (metal) - replace", 31000),
                         ("Headlamp Assembly (plastic)", 11000), ("Denting and Fitting Labour", 9000)],
                  expected="RECOMMEND_REJECT", story="Driving under the influence exclusion (clause 3.1)"))
    S.append(dict(claim_number="CLM-P-3001", claim_type="property", policy_number="CS-HOM-25-003101", claimant="Anita Desai",
                  incident_date="2025-08-21",
                  form_extra={"Property Address": "14 Lake View Road, Pune (fictional)", "Value of Property at Risk": "INR 3,000,000.00"},
                  narrative="A fire started in the kitchen after an electrical short circuit; the kitchen, part of the living room and several appliances were damaged.",
                  items=[("Kitchen Wall and Ceiling Plaster Repair", 145000), ("Kitchen Platform Rebuild (granite and masonry)", 98000),
                         ("Electrical Wiring Replacement", 42000), ("Refrigerator (double door)", 58000), ("Microwave Oven", 14000),
                         ("Sofa Set and Curtains", 66000), ("Debris Removal and Repainting", 27000)],
                  survey="Fire originated at the refrigerator power point. Cause is accidental. Rebuilding cost of the house and contents as new is assessed at INR 30 lakh against a sum insured of INR 25 lakh.",
                  expected="PARTIAL_APPROVAL", story="Fire loss with contents depreciation and the average clause for underinsurance (2.3)"))
    S.append(dict(claim_number="CLM-P-3002", claim_type="property", policy_number="CS-HOM-24-003145", claimant="Vikram Singh",
                  incident_date="2025-06-14", fir="FIR-SYN-0614-31",
                  form_extra={"Property Address": "7 Palm Grove, Jaipur (fictional)", "Value of Property at Risk": "INR 1,100,000.00"},
                  narrative="The house was broken into while the family was away for the weekend; the rear door lock was forced and electronics and jewellery were stolen.",
                  items=[("Laptop Computer", 85000), ("LED Television 55 inch", 62000), ("Gold Jewellery (unscheduled)", 140000),
                         ("Rear Door Lock and Frame Repair", 18000)],
                  survey="Forced entry through the rear door is confirmed. Stolen items are supported by purchase invoices.",
                  police="Forced entry through the rear door confirmed. Case registered for housebreaking and theft.",
                  expected="PARTIAL_APPROVAL", story="Burglary: unscheduled jewellery not covered (3.5), depreciation on electronics, excess"))
    S.append(dict(claim_number="CLM-P-3003", claim_type="property", policy_number="CS-HOM-24-002877", claimant="Lakshmi Menon",
                  incident_date="2025-09-30",
                  form_extra={"Property Address": "22 Temple Street, Kochi (fictional)", "Value of Property at Risk": "INR 1,600,000.00"},
                  narrative="Damp patches and peeling plaster were noticed on the bedroom wall and ceiling after the monsoon.",
                  items=[("Bedroom Wall Plaster and Repaint", 38000), ("Ceiling Repair", 24000), ("Wardrobe Panel Replacement", 21000)],
                  survey="Damage is due to long-term seepage through the terrace slab and gradual deterioration of the waterproofing. No sudden bursting of pipes or tanks was found.",
                  expected="RECOMMEND_REJECT", story="Seepage and gradual deterioration exclusion (3.1)"))
    S.append(dict(claim_number="CLM-T-4001", claim_type="travel", policy_number="CS-TRV-25-004410", claimant="Rahul Verma",
                  incident_date="2025-09-09",
                  form_extra={"Destination": "Singapore", "Departure Date": "2025-09-01", "Return Date": "2025-09-20"},
                  narrative="Severe abdominal pain during a business trip; admitted through emergency and operated for acute appendicitis.",
                  items=[("Emergency Room Assessment", 28000), ("Hospital Room Charges (3 days)", 126000),
                         ("Surgeon and Anaesthetist Fees", 210000), ("Pharmacy and Medicines", 34000),
                         ("Laboratory and CT Scan", 41000), ("Telephone and Toiletries", 3500)],
                  medical=dict(hospital="Marina Bay General Hospital (fictional)", admit="2025-09-09", disch="2025-09-12",
                               diagnosis="Acute appendicitis", procedure="Laparoscopic appendicectomy",
                               notes="No history of abdominal complaints before travel. Fit to fly on 2025-09-15."),
                  expected="PARTIAL_APPROVAL", story="Emergency surgery abroad: personal comfort items not payable (2.4), deductible"))
    S.append(dict(claim_number="CLM-T-4002", claim_type="travel", policy_number="CS-TRV-25-004468", claimant="Neha Kapoor",
                  incident_date="2025-10-05",
                  form_extra={"Destination": "London", "Departure Date": "2025-10-05", "Return Date": "2025-10-19"},
                  narrative="Checked suitcase did not arrive at London Heathrow and was declared lost by the airline after 21 days.",
                  items=[("Checked Suitcase (hard shell)", 18000), ("Laptop Computer", 85000), ("Clothing", 24000),
                         ("Camera with Lens", 40000), ("Shoes and Accessories", 14000)],
                  pir_ref="LHRSY12345",
                  pir="Bag tag traced to the transfer point. Declared permanently lost on 2025-10-26.",
                  expected="PARTIAL_APPROVAL", story="Lost baggage: per-item limit and per-trip baggage limit (2.3)"))
    S.append(dict(claim_number="CLM-T-4003", claim_type="travel", policy_number="CS-TRV-25-004502", claimant="Aditya Joshi",
                  incident_date="2025-08-17",
                  form_extra={"Destination": "Interlaken, Switzerland", "Departure Date": "2025-08-10", "Return Date": "2025-08-24"},
                  narrative="Injured in a paragliding accident near Interlaken; fractured left ankle and treated in hospital.",
                  items=[("Emergency Treatment and Casting", 95000), ("Hospital Room Charges (2 days)", 84000),
                         ("X-Ray and Diagnostic Imaging", 22000)],
                  medical=dict(hospital="Bernese Oberland Clinic (fictional)", admit="2025-08-17", disch="2025-08-19",
                               diagnosis="Fracture of left ankle", procedure="Closed reduction and casting",
                               notes="Injury sustained during a tandem paragliding flight."),
                  expected="RECOMMEND_REJECT", story="Hazardous sports exclusion (3.2)"))
    S.append(dict(claim_number="CLM-T-4004", claim_type="travel", policy_number="CS-TRV-25-004533", claimant="Sana Qureshi",
                  incident_date="2025-11-02",
                  form_extra={"Destination": "Dubai", "Departure Date": "2025-11-02", "Return Date": "2025-11-12"},
                  narrative="Checked baggage was lost on arrival at Dubai; the airline has not traced it.",
                  items=[("Checked Suitcase", 12000), ("Clothing", 22000), ("Shoes and Accessories", 9000)],
                  expected="REQUEST_INFO", story="Baggage claim without the airline's property irregularity report (5.2)"))
    S.append(dict(claim_number="CLM-H-1007", claim_type="health", policy_number="CS-HLT-24-000611", claimant="Divya Pillai",
                  incident_date="2025-07-22", hospital="Greenfield General Hospital (fictional)",
                  narrative="Admitted at full term and delivered by caesarean section.",
                  items=[("Room Rent - Twin Sharing (3 days @ 4,500)", 13500), ("Obstetrician and Anaesthetist Fees", 40000),
                         ("Operation Theatre Charges", 15000), ("Pharmacy - Medicines and Drugs", 9000)],
                  admit="2025-07-22", disch="2025-07-25", diagnosis="Full term pregnancy",
                  procedure="Lower segment caesarean section", notes="Mother and baby discharged in good health.",
                  expected="RECOMMEND_REJECT", story="Maternity and childbirth exclusion (4.4)"))
    S.append(dict(claim_number="CLM-M-2003", claim_type="motor", policy_number="CS-MTR-25-001452", claimant="Rohan Gupta",
                  incident_date="2025-10-03", fir="FIR-SYN-1003-14", licence_valid_till="2024-12-31",
                  form_extra={"Vehicle Registration": "KA-01-SY-7733", "Vehicle Make and Model": "Hatchback 1199cc",
                              "Date of First Registration": "2023-08-19", "Engine Capacity cc": "1199"},
                  narrative="Skidded on a wet road and hit a parked truck; front bumper, bonnet and headlamp damaged.",
                  police="Collision confirmed. The driver's licence expired on 2024-12-31; no valid licence at the time of the accident.",
                  items=[("Front Bumper (plastic) - replace", 13000), ("Bonnet (metal) - replace", 28000),
                         ("Headlamp Assembly (plastic)", 9500), ("Denting and Fitting Labour", 8000)],
                  expected="RECOMMEND_REJECT", story="Driver without a valid licence exclusion (3.2)"))
    S.append(dict(claim_number="CLM-P-3004", claim_type="property", policy_number="CS-HOM-25-003260", claimant="Farhan Ali",
                  incident_date="2025-09-12", fir="FIR-SYN-0912-27",
                  form_extra={"Property Address": "3 Hill View Colony, Hyderabad (fictional)", "Value of Property at Risk": "INR 1,400,000.00"},
                  narrative="The house was broken into and electronics were stolen while the family was abroad; it had been unoccupied since early June.",
                  items=[("LED Television 50 inch", 70000), ("Laptop Computer", 90000), ("Window Grill and Lock Repair", 12000)],
                  survey="Forced entry through a rear window is confirmed. The premises were unoccupied for about 95 days before the loss was discovered.",
                  police="Forced entry through a rear window confirmed. Case registered for housebreaking and theft.",
                  expected="RECOMMEND_REJECT", story="Unoccupied premises exclusion (3.3)"))
    S.append(dict(claim_number="CLM-T-4005", claim_type="travel", policy_number="CS-TRV-25-004611", claimant="Gopal Krishnan",
                  incident_date="2025-12-06",
                  form_extra={"Destination": "Toronto", "Departure Date": "2025-12-01", "Return Date": "2025-12-15"},
                  narrative="Chest pain in Toronto; admitted to hospital for a known heart condition that was under treatment before departure.",
                  items=[("Emergency Room Assessment", 35000), ("Hospital Room Charges (2 days)", 98000),
                         ("Diagnostic Cardiology Tests and Angiogram", 145000)],
                  medical=dict(hospital="Lakeshore General Hospital (fictional)", admit="2025-12-06", disch="2025-12-08",
                               diagnosis="Unstable angina in known coronary artery disease", procedure="Coronary angiography",
                               notes="Known case of coronary artery disease on medication for three years; a pre-existing condition."),
                  expected="RECOMMEND_REJECT", story="Pre-existing condition exclusion (3.1)"))
    return S


def write_claim_packets() -> list[dict]:
    out = []
    for c in golden_claims():
        d = CLM / c["claim_number"]
        d.mkdir(parents=True, exist_ok=True)
        total = sum(a for _, a in c["items"])
        c.setdefault("form_amount", total)
        files = {}
        files["claim_form.txt"] = claim_form(c)
        if c["claim_type"] in ("property", "travel"):
            files.update(line_documents(c))
        elif c["claim_type"] == "health":
            files["hospital_bill.txt"] = bill("FINAL HOSPITAL BILL", c, c["items"],
                                              {"Hospital": c["hospital"], "Bill Number": f"HB-{c['claim_number'][-4:]}",
                                               "Admission Date": c["admit"], "Discharge Date": c["disch"]})
            if not c.get("skip_discharge"):
                files["discharge_summary.txt"] = discharge(c, c["admit"], c["disch"], c["diagnosis"], c["procedure"], c["notes"])
        else:
            files["repair_estimate.txt"] = bill("WORKSHOP REPAIR ESTIMATE", c, c["items"],
                                                {"Workshop": "Ring Road Auto Works (fictional)",
                                                 "Estimate Number": f"RE-{c['claim_number'][-4:]}",
                                                 "Vehicle Registration": c["form_extra"]["Vehicle Registration"]})
            files["driving_licence.txt"] = licence(c)
            files["police_report.txt"] = police_report(c, c.get("police", "Collision confirmed. No injuries reported."))
        for name, body in files.items():
            (d / name).write_text(body, encoding="utf-8")
        # one PDF copy so the PDF extraction path is exercised by the demo and tests
        if c["claim_number"] == "CLM-H-1001":
            write_pdf(d / "hospital_bill.pdf", files.pop("hospital_bill.txt").splitlines())
            (d / "hospital_bill.txt").unlink()
            files["hospital_bill.pdf"] = None
        out.append({"claim_number": c["claim_number"], "claim_type": c["claim_type"], "policy_number": c["policy_number"],
                    "claimant_name": c["claimant"], "incident_date": c["incident_date"], "description": c["narrative"],
                    "documents": sorted(files), "expected_recommendation": c["expected"], "scenario": c["story"]})
    return out


def write_demo_upload() -> None:
    """A packet that is NOT seeded, for uploading live through the UI during a demo."""
    c = dict(claim_number="DEMO-UPLOAD", claim_type="health", policy_number="CS-HLT-23-000089", claimant="Fatima Shaikh",
             incident_date="2025-11-03", hospital="Riverside Urology Centre (fictional)",
             narrative="Severe flank pain; admitted and treated for a left kidney stone.")
    items = [("Room Rent - Twin Sharing (2 days @ 4,800)", 9600), ("Urologist and Anaesthetist Fees", 38000),
             ("Operation Theatre Charges", 15000), ("Pharmacy - Medicines and Drugs", 7400),
             ("Diagnostic Tests - CT KUB and Urine Culture", 6200), ("Admission Kit and Consumables", 1800)]
    c["form_amount"] = sum(a for _, a in items)
    d = CLM / "demo_upload"
    d.mkdir(parents=True, exist_ok=True)
    (d / "claim_form.txt").write_text(claim_form(c), encoding="utf-8")
    (d / "hospital_bill.txt").write_text(bill("FINAL HOSPITAL BILL", c, items, {"Hospital": c["hospital"], "Bill Number": "HB-7781",
                                              "Admission Date": "2025-11-03", "Discharge Date": "2025-11-05"}), encoding="utf-8")
    (d / "discharge_summary.txt").write_text(discharge(c, "2025-11-03", "2025-11-05", "Left renal calculus (kidney stone), 9 mm",
                                                       "Ureteroscopic lithotripsy (URSL)", "Stone cleared. Discharged with stent."), encoding="utf-8")


def evaluation_claims() -> list[dict]:
    """Packets for evaluation cases the seeded scenarios do not cover. Created fresh by scripts/evaluate.py."""
    viral = [("Room Rent - Twin Sharing (3 days @ 4,500)", 13500), ("Consultant Physician Fees", 9000),
             ("Pharmacy - Medicines and Drugs", 8200), ("Laboratory Tests - Platelet Count and Serology", 5300)]
    E = []
    E.append(dict(claim_number="EVAL-H-01", claim_type="health", policy_number="CS-HLT-24-000233", claimant="Suresh Nair",
                  incident_date="2025-11-10", hospital="Lakeview Multispeciality Hospital (fictional)",
                  narrative="Admitted with acute gastroenteritis and dehydration after two days of vomiting.",
                  items=[("Room Rent - General Ward (2 days @ 4,000)", 8000), ("Consultant Physician Fees", 6000),
                         ("Pharmacy - Medicines and IV Fluids", 7400), ("Laboratory Tests - Stool and Blood", 3600)],
                  admit="2025-11-10", disch="2025-11-12", diagnosis="Acute gastroenteritis with moderate dehydration",
                  procedure="Medical management with IV fluids", notes="Recovered. Discharged on oral rehydration."))
    E.append(dict(claim_number="EVAL-H-02", claim_type="health", policy_number="CS-HLT-25-000342", claimant="Meena Iyer",
                  incident_date="2025-12-05", hospital="Sunrise Care Hospital (fictional)",
                  narrative="Injured in a road traffic accident as a pillion rider; fractures of the left femur and pelvis.",
                  items=[("Room Rent - Twin Sharing (8 days @ 5,000)", 40000), ("ICU Charges (3 days @ 10,000)", 30000),
                         ("Orthopaedic Surgeon and Anaesthetist Fees", 120000), ("Operation Theatre Charges", 45000),
                         ("Implants - Femur Nail and Pelvic Plates", 110000), ("Pharmacy - Medicines and Drugs", 38000),
                         ("Physiotherapy and Diagnostic Imaging", 27000)],
                  admit="2025-12-05", disch="2025-12-16",
                  diagnosis="Fracture shaft of left femur and pelvic fracture following road traffic accident",
                  procedure="Intramedullary nailing of femur and pelvic fixation", notes="Mobilised with walker. Discharged."))
    for number, day, disch in (("EVAL-H-03", "2025-04-01", "2025-04-04"), ("EVAL-H-04", "2025-03-31", "2025-04-03")):
        E.append(dict(claim_number=number, claim_type="health", policy_number="CS-HLT-24-000117", claimant="Ravi Kumar",
                      incident_date=day, hospital="Greenfield General Hospital (fictional)",
                      narrative="High-grade fever with body ache; admitted for viral fever with low platelets.",
                      items=viral, admit=day, disch=disch, diagnosis="Viral fever with thrombocytopenia",
                      procedure="Medical management", notes="Platelets recovered. Discharged."))
    E.append(dict(claim_number="EVAL-P-01", claim_type="property", policy_number="CS-HOM-24-002877", claimant="Lakshmi Menon",
                  incident_date="2025-07-14",
                  form_extra={"Property Address": "22 Temple Street, Kochi (fictional)", "Value of Property at Risk": "INR 1,600,000.00"},
                  narrative="A storm with high winds blew off part of the roof and damaged the ceiling of the living room.",
                  items=[("Roof Sheet Replacement", 46000), ("Ceiling Plaster Repair", 19000), ("Debris Removal", 6000)],
                  survey="Storm damage is confirmed by the weather bulletin for the date of loss. Repairs are reasonable."))
    E.append(dict(claim_number="EVAL-T-01", claim_type="travel", policy_number="CS-TRV-25-004588", claimant="Kavya Reddy",
                  incident_date="2025-12-20",
                  form_extra={"Destination": "Tokyo", "Departure Date": "2025-12-20", "Return Date": "2026-01-03"},
                  narrative="The departure flight to Tokyo was cancelled after the airport was closed by the authorities for a cyclone; the trip could not be taken.",
                  items=[("Non-refundable Airfare", 112000), ("Hotel Booking (non-refundable)", 68000)]))
    E.append(dict(claim_number="EVAL-T-02", claim_type="travel", policy_number="CS-TRV-25-004588", claimant="Kavya Reddy",
                  incident_date="2026-02-12",
                  form_extra={"Destination": "Bangkok", "Departure Date": "2026-02-02", "Return Date": "2026-02-09"},
                  narrative="Treated at a clinic for a sprained knee three days after the trip ended, during an extended personal stay in Bangkok.",
                  items=[("Clinic Consultation and X-Ray", 9500), ("Pharmacy and Medicines", 2500)]))
    return E


def write_evaluation_packets() -> None:
    for c in evaluation_claims():
        d = EVAL / c["claim_number"]
        d.mkdir(parents=True, exist_ok=True)
        c["form_amount"] = sum(a for _, a in c["items"])
        if c["claim_type"] in ("property", "travel"):
            for name, body in line_documents(c).items():
                (d / name).write_text(body, encoding="utf-8")
            continue
        (d / "claim_form.txt").write_text(claim_form(c), encoding="utf-8")
        (d / "hospital_bill.txt").write_text(bill("FINAL HOSPITAL BILL", c, c["items"],
                                                  {"Hospital": c["hospital"], "Bill Number": f"HB-{c['claim_number'][-4:]}",
                                                   "Admission Date": c["admit"], "Discharge Date": c["disch"]}), encoding="utf-8")
        (d / "discharge_summary.txt").write_text(discharge(c, c["admit"], c["disch"], c["diagnosis"], c["procedure"], c["notes"]),
                                                 encoding="utf-8")


def write_pdf(path: Path, lines: list[str]) -> None:
    """Minimal single-page text PDF (Courier), enough for pypdf text extraction."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace").decode("latin-1")
    content = ["BT", "/F1 9 Tf", "11 TL", "40 800 Td"] + [f"({esc(line)}) Tj T*" for line in lines] + ["ET"]
    stream = "\n".join(content).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def policy_pdf_pages(markdown: str, width: int = 92) -> list[list[str]]:
    """Lay out policy wording as plain PDF pages: headings become numbered lines, body text is wrapped."""
    import textwrap
    pages: list[list[str]] = [[]]
    for line in markdown.splitlines():
        if line.startswith("<!-- page:"):
            if int(line.split(":")[1].split("-")[0]) > 1:
                pages.append([])
            continue
        text = line.lstrip("#").strip().replace("\u2014", "-")
        if line.startswith("#") or not text:
            pages[-1].append(text)
        else:
            pages[-1].extend(textwrap.wrap(text, width, break_on_hyphens=False))
    return [p for p in pages if any(x.strip() for x in p)]


def write_pdf_pages(path: Path, pages: list[list[str]]) -> None:
    """Multi-page text PDF (Courier 9pt), one content stream per page, readable by pypdf."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace").decode("latin-1")
    n = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode()]
    font = 3 + 2 * n
    for i, lines in enumerate(pages):
        content = ["BT", "/F1 9 Tf", "11 TL", "40 800 Td"] + [f"({esc(line)}) Tj T*" for line in lines] + ["ET"]
        stream = "\n".join(content).encode("latin-1")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font} 0 R >> >> "
                    f"/Contents {4 + 2 * i} 0 R >>".encode())
        objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def write_ingest_demo() -> None:
    v, p = DEMO_INGEST_VERSION
    d = POL / "ingest_demo"
    d.mkdir(parents=True, exist_ok=True)
    write_pdf_pages(d / f"HLT-SHIELD_{v}.pdf", policy_pdf_pages(health_wording(v, p)))
    (d / f"HLT-SHIELD_{v}.terms.json").write_text(json.dumps(health_terms(v, p), indent=2), encoding="utf-8")


# ------------------------------------------------------------ portfolio ---
PATTERNS = ["AMOUNT_ANOMALY", "TIMING_ANOMALY", "FREQUENCY_ANOMALY", "DUPLICATE_CLAIM", "DOCUMENT_INCONSISTENCY"]
# line: (share of claims, sums insured, log-normal mean of the claim amount)
PORTFOLIO_LINES = {
    "health": (0.50, [300000, 500000, 1000000], 10.6),
    "motor": (0.25, [350000, 500000, 800000], 10.2),
    "property": (0.13, [1000000, 2500000, 5000000], 11.2),
    "travel": (0.12, [2000000, 4000000], 10.4),
}


def portfolio(n: int = 1000, fraud_rate: float = 0.08) -> None:
    """Synthetic claim portfolio with labelled, injected anomaly patterns.

    The injection rate is a demo parameter, not an estimate of real-world fraud prevalence.
    """
    rng = random.Random(2025)
    rows = []
    for i in range(1, n + 1):
        line = rng.choices(list(PORTFOLIO_LINES), [v[0] for v in PORTFOLIO_LINES.values()])[0]
        _, sums, mu = PORTFOLIO_LINES[line]
        si = rng.choice(sums)
        start = date(2024, 4, 1) + timedelta(days=rng.randint(0, 420))
        # a travel policy starts at departure, so the loss falls within the trip
        incident = start + timedelta(days=rng.randint(1, 30) if line == "travel" else rng.randint(45, 330))
        amount = round(min(si * 0.9, rng.lognormvariate(mu, 0.6)), -2)
        prior = rng.choices([0, 1, 2], [0.8, 0.15, 0.05])[0]
        bill_total, dup = amount, 0
        injected: list[str] = []
        if rng.random() < fraud_rate:
            # the risk rules do not score timing for trip-based cover, so no timing anomaly is injected there
            patterns = [x for x in PATTERNS if not (line == "travel" and x == "TIMING_ANOMALY")]
            injected = rng.sample(patterns, rng.choice([1, 1, 2]))
            if "AMOUNT_ANOMALY" in injected:
                amount = round(si * rng.uniform(0.82, 0.99), -2)
                bill_total = amount
            if "TIMING_ANOMALY" in injected:
                incident = start + timedelta(days=rng.randint(31, 55))
            if "FREQUENCY_ANOMALY" in injected:
                prior = rng.randint(3, 5)
            if "DUPLICATE_CLAIM" in injected:
                dup = 1
            if "DOCUMENT_INCONSISTENCY" in injected:
                bill_total = round(amount * rng.uniform(0.7, 0.9), -2)
        rows.append({
            "claim_id": f"SYN-{i:06d}", "line_of_business": line, "sum_insured": si,
            "policy_start": start.isoformat(), "incident_date": incident.isoformat(),
            "days_since_policy_start": (incident - start).days, "claimed_amount": int(amount),
            "document_total": int(bill_total), "prior_claims_12m": prior, "duplicate_match": dup,
            "fraud_label": 1 if injected else 0, "injected_patterns": "|".join(injected),
        })
    with (SYN / "claims_portfolio.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    POL.mkdir(parents=True, exist_ok=True)
    CLM.mkdir(parents=True, exist_ok=True)
    for v, p in HEALTH_VERSIONS.items():
        (POL / f"HLT-SHIELD_{v}.md").write_text(health_wording(v, p), encoding="utf-8")
        (POL / f"HLT-SHIELD_{v}.terms.json").write_text(json.dumps(health_terms(v, p), indent=2), encoding="utf-8")
    (POL / "MTR-SECURE_2025.1.md").write_text(motor_wording(), encoding="utf-8")
    (POL / "MTR-SECURE_2025.1.terms.json").write_text(json.dumps(motor_terms(), indent=2), encoding="utf-8")
    (POL / "HOME-GUARD_2025.1.md").write_text(property_wording(), encoding="utf-8")
    (POL / "HOME-GUARD_2025.1.terms.json").write_text(json.dumps(property_terms(), indent=2), encoding="utf-8")
    (POL / "TRV-GLOBE_2025.1.md").write_text(travel_wording(), encoding="utf-8")
    (POL / "TRV-GLOBE_2025.1.terms.json").write_text(json.dumps(travel_terms(), indent=2), encoding="utf-8")
    (POL / "insured_policies.json").write_text(json.dumps([
        dict(policy_number=a, product_code=b, holder_name=c, start_date=d, end_date=e, sum_insured=f)
        for a, b, c, d, e, f in INSURED], indent=2), encoding="utf-8")
    scen = write_claim_packets()
    write_demo_upload()
    write_evaluation_packets()
    write_ingest_demo()
    (CLM / "scenarios.json").write_text(json.dumps(scen, indent=2), encoding="utf-8")
    portfolio()
    print(f"policies: {len(list(POL.glob('*.md')))}, claims: {len(scen)}, portfolio rows: 1000")


if __name__ == "__main__":
    main()
