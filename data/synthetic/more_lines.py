"""Synthetic travel, home, personal accident and life products for the Claim Sense demo.

Same rules as generate.py: a fictional insurer, fictional people and wording written for this demo. The wording
borrows common Indian retail-insurance concepts (trip-delay and baggage sub-limits, the average clause for
under-insurance, capital-sum benefit tables, the suicide exclusion and the three-year limit in section 45 of the
Insurance Act, 1938) but it is not any insurer's product and not regulatory text.

Imported by generate.py; every claim here is designed to reach the outcome in its `expected` field, which
backend/tests/test_demo_book.py checks after seeding.
"""
from __future__ import annotations

from datetime import date, timedelta

INSURER = "Synthetic Assurance Co. Ltd. (fictional)"
NOTICE = ("This is SYNTHETIC policy wording created for the Claim Sense demo. It is not issued by any "
          "real insurer and is not regulatory text.")
VERSION, FROM, TO = "2026.1", "2026-04-01", "2027-03-31"
# demo-book filing dates are counted back from the seeding day; incidents must precede them from this day on
REFERENCE_DAY = date(2026, 10, 11)
MEDICAL = ["room_rent", "icu", "professional_fees", "ot_charges", "medicines", "diagnostics", "equipment", "consumables"]


def _head(name: str, code: str, kind: str) -> str:
    return f"""# {name} — {kind} (Version {VERSION})

<!-- page: 1 -->
## 1. Preamble and Definitions

### 1.1 Insurer and Policy
This policy is issued by {INSURER}. Product code {code}, wording version {VERSION}, effective for policies incepting from {FROM} to {TO}. {NOTICE}
"""


def _base(code: str, name: str, line: str, model: str) -> dict:
    return {"product_code": code, "product_name": name, "line_of_business": line, "adjudication_model": model,
            "insurer": INSURER, "version": VERSION, "effective_from": FROM, "effective_to": TO}


# ---------------------------------------------------------------- travel ---
def travel_wording() -> str:
    return _head("ClaimSense Travel Globe", "TRV-GLOBE", "Overseas Travel Insurance Policy Wording") + """
### 1.2 Period of Cover
Cover runs from the trip start date to the trip end date shown in the schedule. Only events that occur during this period, while the insured person is outside India, are covered.

### 1.3 Sum Insured
The sum insured stated in the schedule is the most the insurer will pay for all claims during the trip, for all benefits together.

<!-- page: 2 -->
## 2. Benefits

### 2.1 Emergency Medical Expenses
The insurer will pay reasonable and customary charges for emergency treatment of a sudden illness or an accidental injury that occurs during the trip, including hospital room, intensive care, doctors' and surgeons' fees, operation theatre charges, medicines and diagnostic tests. Only the benefits listed in this section are covered.

### 2.2 Emergency Medical Evacuation
Medically necessary evacuation by air ambulance to the nearest suitable hospital or back to India is covered up to INR 5,00,000 per trip.

### 2.3 Loss of Checked Baggage
Permanent loss of checked baggage while in the custody of the airline is covered up to INR 50,000 per trip and INR 15,000 for any one item. Depreciation of 10% is deducted from the value of each lost item. A property irregularity report from the airline is required.

### 2.4 Trip Delay
When a scheduled flight is delayed by more than 12 hours, reasonable expenses for meals and accommodation are reimbursed up to INR 10,000 per trip.

### 2.5 Trip Cancellation
Non-refundable prepaid travel and accommodation costs are reimbursed up to INR 1,00,000 if the trip is cancelled because the insured person or a member of their immediate family dies or is hospitalised.

### 2.6 Loss of Passport
The cost of obtaining a duplicate passport or an emergency travel document is reimbursed up to INR 15,000.

<!-- page: 3 -->
## 3. Deductible and Exclusions

### 3.1 Deductible
A deductible of INR 5,000 applies to each claim for emergency medical expenses. No deductible applies to the other benefits.

### 3.2 Pre-existing Conditions
Treatment of any pre-existing condition, or any complication of it, is not covered.

### 3.3 Hazardous Activities
Injury sustained while taking part in scuba diving, skydiving, bungee jumping, paragliding or mountaineering is not covered.

### 3.4 Alcohol and Drugs
Any claim arising while the insured person is under the influence of alcohol or drugs is not covered.

### 3.5 Travel Against Medical Advice
Treatment needed because the insured person travelled against medical advice, or travelled to obtain treatment, is not covered.

### 3.6 Non-medical Charges
Registration charges, food for attendants and other non-medical items on a hospital bill are not payable.

<!-- page: 4 -->
## 4. Claims Procedure

### 4.1 Claim Intimation
The insured person must notify the assistance helpline within 48 hours of a hospitalisation and submit the claim within 30 days of returning to India.

### 4.2 Documents Required
A claim must include the claim form, a copy of the passport with entry and exit stamps and the travel ticket or itinerary, together with the bills and reports for the benefit claimed.

### 4.3 Claim Settlement
The insurer will settle the claim within 30 days of receiving all necessary documents.
"""


def travel_terms() -> dict:
    return {
        **_base("TRV-GLOBE", "ClaimSense Travel Globe", "travel", "indemnity"),
        "covered_categories": {"categories": MEDICAL + ["emergency_evacuation", "baggage", "trip_delay",
                                                        "trip_cancellation", "passport_loss"], "clause": "2.1"},
        "non_payable_categories": {"non_medical": "3.6"},
        "depreciation": {"clause": "2.3", "flat_percent": {"baggage": 10}},
        "item_caps": {"baggage": {"amount": 15000, "clause": "2.3"}},
        "category_caps": {"emergency_evacuation": {"amount": 500000, "clause": "2.2"},
                          "baggage": {"amount": 50000, "clause": "2.3"}, "trip_delay": {"amount": 10000, "clause": "2.4"},
                          "trip_cancellation": {"amount": 100000, "clause": "2.5"},
                          "passport_loss": {"amount": 15000, "clause": "2.6"}},
        "deductible": {"amount": 5000, "clause": "3.1", "applies_to": MEDICAL},
        "max_liability_clause": "1.3",
        # a trip policy starts with the trip, so a claim soon after the start is normal
        "early_claim_days": 0,
        "exclusions": [
            {"code": "EXCL_PRE_EXISTING", "clause": "3.2", "keywords": ["pre-existing", "known case of"]},
            {"code": "EXCL_HAZARDOUS_ACTIVITY", "clause": "3.3",
             "keywords": ["scuba", "skydiving", "bungee", "paragliding", "mountaineering"]},
            {"code": "EXCL_ALCOHOL", "clause": "3.4", "keywords": ["under the influence", "intoxicated"]},
            {"code": "EXCL_MEDICAL_ADVICE", "clause": "3.5", "keywords": ["against medical advice", "travelled for treatment"]},
        ],
        "required_documents": {"documents": ["claim_form", "passport_copy", "travel_ticket"], "clause": "4.2"},
        "settlement_days": {"value": 30, "clause": "4.3"},
        "coverage_clause": "1.2",
    }


# ------------------------------------------------------------------ home ---
def home_wording() -> str:
    return _head("ClaimSense Home Shield", "HOME-SHIELD", "Householder's Package Policy Wording") + """
### 1.2 Sum Insured
The sum insured for the building and its contents is stated in the schedule. The insurer's liability for all claims in the policy period shall not exceed the sum insured.

### 1.3 Under-insurance (Average)
If at the time of loss the value at risk of the property exceeds the sum insured, the insured is considered to be their own insurer for the difference and bears a rateable proportion of the loss.

<!-- page: 2 -->
## 2. Cover

### 2.1 Insured Perils
The insurer will indemnify the insured for physical loss of or damage to the building and contents at the address in the schedule caused by fire, lightning, explosion, storm, flood, inundation, burglary or housebreaking, or impact. Only the losses listed in this section are covered.

### 2.2 Depreciation on Contents
Depreciation is deducted from the replacement cost of contents: 15% on electronic items, 10% on appliances and furniture, and 25% on clothing. Repairs to the building are paid at reinstatement cost without depreciation.

### 2.3 Jewellery and Valuables
Jewellery and valuables kept in a locked safe are covered up to INR 1,00,000 in all for the policy period.

### 2.4 Removal of Debris
The cost of removing debris after an insured loss is covered up to INR 50,000.

### 2.5 Alternative Accommodation
If the home cannot be lived in after an insured loss, rent for alternative accommodation is reimbursed up to INR 25,000 a month for at most three months, INR 75,000 in all.

<!-- page: 3 -->
## 3. Deductible and Exclusions

### 3.1 Deductible
A deductible of INR 10,000 applies to each claim.

### 3.2 Wear, Tear and Gradual Deterioration
Wear and tear, gradual deterioration, seepage, termite damage, rusting and poor maintenance are not covered.

### 3.3 Unoccupied Premises
Burglary or damage while the home has been left unoccupied for more than 30 consecutive days is not covered.

### 3.4 War and Nuclear Risks
Loss caused by an act of war, invasion, civil war or nuclear radiation is not covered.

### 3.5 Wilful Acts
Loss caused deliberately by the insured or with their connivance is not covered.

<!-- page: 4 -->
## 4. Claims Procedure

### 4.1 Claim Intimation
The insured must notify the insurer within 7 days of the loss. Burglary must also be reported to the police and a copy of the first information report (FIR) submitted.

### 4.2 Documents Required
A claim must include the claim form, a statement of loss listing each item and its replacement or repair cost, and the report of the surveyor appointed by the insurer.

### 4.3 Claim Settlement
The insurer will settle the claim within 30 days of receiving the survey report and all necessary documents.
"""


def home_terms() -> dict:
    return {
        **_base("HOME-SHIELD", "ClaimSense Home Shield", "home", "indemnity"),
        "covered_categories": {"categories": ["building_repair", "contents_electronics", "contents_appliance",
                                              "contents_furniture", "contents_clothing", "jewellery",
                                              "debris_removal", "alt_accommodation"], "clause": "2.1"},
        "depreciation": {"clause": "2.2", "flat_percent": {"contents_electronics": 15, "contents_appliance": 10,
                                                           "contents_furniture": 10, "contents_clothing": 25}},
        "category_caps": {"jewellery": {"amount": 100000, "clause": "2.3"},
                          "debris_removal": {"amount": 50000, "clause": "2.4"},
                          "alt_accommodation": {"amount": 75000, "clause": "2.5"}},
        "average": {"clause": "1.3"},
        "deductible": {"amount": 10000, "clause": "3.1"},
        "max_liability_clause": "1.2",
        "exclusions": [
            {"code": "EXCL_WEAR_TEAR", "clause": "3.2",
             "keywords": ["wear and tear", "gradual", "seepage", "termite", "rusting", "poor maintenance"]},
            {"code": "EXCL_UNOCCUPIED", "clause": "3.3", "keywords": ["unoccupied", "locked up for"]},
            {"code": "EXCL_WAR", "clause": "3.4", "keywords": ["act of war", "invasion", "civil war", "nuclear"]},
            {"code": "EXCL_WILFUL", "clause": "3.5", "keywords": ["deliberately", "wilful"]},
        ],
        "required_documents": {"documents": ["claim_form", "claim_statement", "survey_report"], "clause": "4.2"},
        "settlement_days": {"value": 30, "clause": "4.3"},
        "coverage_clause": "2.1",
    }


# ----------------------------------------------------- personal accident ---
PPD_TABLE = [(["one hand", "one foot", "one eye", "one arm", "one leg"], 50), (["thumb"], 25),
             (["index finger"], 10), (["hearing in one ear"], 15), (["big toe"], 5), (["finger"], 5)]


def pa_wording() -> str:
    return _head("ClaimSense Personal Accident Secure", "PA-SECURE", "Personal Accident Policy Wording") + """
### 1.2 Capital Sum Insured
Benefits are a percentage of the capital sum insured stated in the schedule. The total paid for all claims in the policy period shall not exceed 100% of the capital sum insured. No deductible applies to any benefit.

### 1.3 Accident
Accident means a sudden, unforeseen and involuntary event caused by external, violent and visible means. The policy covers bodily injury caused solely and directly by an accident; illness and disease are not covered.

<!-- page: 2 -->
## 2. Benefits

### 2.1 Accidental Death
If injury results in death within 12 months of the accident, 100% of the capital sum insured is paid to the nominee.

### 2.2 Permanent Total Disablement
If injury results in permanent total disablement, such as the loss of both hands, both feet or the sight of both eyes, 100% of the capital sum insured is paid.

### 2.3 Permanent Partial Disablement
For permanent partial disablement the following percentages of the capital sum insured are paid: loss of one hand, one foot, one arm, one leg or the sight of one eye, 50%; loss of a thumb, 25%; total loss of hearing in one ear, 15%; loss of an index finger, 10%; loss of any other finger or of a big toe, 5%.

### 2.4 Temporary Total Disablement
If injury prevents the insured from working at all, 1% of the capital sum insured is paid for each week of disablement, up to INR 10,000 a week and for at most 100 weeks.

### 2.5 Accident Medical Expenses
Medical expenses for treating an injury covered by this policy are reimbursed up to 10% of the capital sum insured.

<!-- page: 3 -->
## 3. Exclusions

### 3.1 Suicide and Self-injury
Suicide, attempted suicide and intentionally self-inflicted injury are not covered.

### 3.2 Alcohol and Drugs
Injury sustained while under the influence of alcohol or drugs is not covered.

### 3.3 Hazardous Sports
Injury sustained in motor racing, speed contests or bungee jumping is not covered.

### 3.4 War
Injury caused by an act of war, invasion or civil war is not covered.

<!-- page: 4 -->
## 4. Claims Procedure

### 4.1 Claim Intimation
The insurer must be notified within 30 days of the accident. Road accidents must be reported to the police.

### 4.2 Documents Required
A claim must include the claim form, a benefit claim statement listing each benefit claimed, and a certificate from the treating doctor describing the injury and the disablement.

### 4.3 Claim Settlement
The insurer will settle the claim within 30 days of receiving all necessary documents.
"""


def pa_terms() -> dict:
    return {
        **_base("PA-SECURE", "ClaimSense Personal Accident Secure", "personal_accident", "benefit_schedule"),
        "accident_only": {"clause": "1.3"},
        "benefits": {
            "accidental_death": {"basis": "percent_of_si", "percent": 100, "clause": "2.1"},
            "ptd": {"basis": "percent_of_si", "percent": 100, "clause": "2.2"},
            "ppd": {"basis": "schedule", "clause": "2.3",
                    "schedule": [{"keywords": k, "percent": p} for k, p in PPD_TABLE]},
            "ttd": {"basis": "weekly", "percent": 1, "weekly_cap": 10000, "max_weeks": 100, "clause": "2.4"},
            "medical_expenses": {"basis": "reimbursement", "percent": 10, "clause": "2.5"},
        },
        "deductible": {"amount": 0, "clause": "1.2"},
        "max_liability_clause": "1.2",
        "exclusions": [
            {"code": "EXCL_SELF_INJURY", "clause": "3.1", "keywords": ["suicide", "self-inflicted"]},
            {"code": "EXCL_ALCOHOL", "clause": "3.2", "keywords": ["under the influence", "intoxicated", "drunk"]},
            {"code": "EXCL_HAZARDOUS_SPORT", "clause": "3.3", "keywords": ["motor racing", "speed contest", "bungee"]},
            {"code": "EXCL_WAR", "clause": "3.4", "keywords": ["act of war", "invasion", "civil war"]},
        ],
        "required_documents": {"documents": ["claim_form", "claim_statement", "medical_certificate"], "clause": "4.2"},
        "settlement_days": {"value": 30, "clause": "4.3"},
        "coverage_clause": "1.3",
    }


# ------------------------------------------------------------------ life ---
def life_wording() -> str:
    return _head("ClaimSense Life Term Protect", "LIFE-TERM", "Term Life Insurance Policy Wording") + """
### 1.2 Sum Assured
The sum assured is the amount stated in the schedule. It is the most the insurer will pay under this policy.

### 1.3 Policy in Force
The policy is in force while premiums are paid within the due date or the 30-day grace period. Cover ends on the expiry date in the schedule.

<!-- page: 2 -->
## 2. Benefit

### 2.1 Death Benefit
If the life assured dies while the policy is in force, the sum assured is paid in full to the nominee, without any deductible. This is the only benefit under the policy.

### 2.2 Nominee
The death benefit is paid to the nominee recorded in the schedule, or to the legal heirs if there is no valid nomination.

<!-- page: 3 -->
## 3. Exclusions and Conditions

### 3.1 Suicide
If the life assured dies by suicide within 12 months of the date of commencement of risk, the death benefit is not payable. The nominee is entitled to 80% of the premiums paid, which is refunded through policy servicing and is not part of a death claim.

### 3.2 Non-disclosure and Section 45
In line with section 45 of the Insurance Act, 1938, the policy cannot be called in question on any ground after three years from the date of the policy. Claims within those three years may be investigated for misstatement or suppression of material facts.

<!-- page: 4 -->
## 4. Claims Procedure

### 4.1 Claim Intimation
The nominee should notify the insurer of the death as soon as possible.

### 4.2 Documents Required
A death claim must include the claim form signed by the nominee, a benefit claim statement, the death certificate issued by the local authority and the certificate of the doctor who attended the life assured.

### 4.3 Claim Settlement
The insurer will settle the claim within 30 days of receiving the last necessary document, or within 120 days when the claim needs investigation.
"""


def life_terms() -> dict:
    return {
        **_base("LIFE-TERM", "ClaimSense Life Term Protect", "life", "benefit_schedule"),
        "benefits": {"death_benefit": {"basis": "percent_of_si", "percent": 100, "clause": "2.1"}},
        "deductible": {"amount": 0, "clause": "2.1"},
        "max_liability_clause": "1.2",
        # section 45 window: early death claims are flagged for review (clause 3.2)
        "early_claim_days": 1095,
        "exclusions": [{"code": "EXCL_SUICIDE", "clause": "3.1", "keywords": ["suicide", "self-inflicted"],
                        "within_months": 12}],
        "required_documents": {"documents": ["claim_form", "claim_statement", "death_certificate", "medical_certificate"],
                               "clause": "4.2"},
        "settlement_days": {"value": 30, "clause": "4.3"},
        "coverage_clause": "1.3",
    }


PRODUCTS = [("TRV-GLOBE", travel_wording, travel_terms), ("HOME-SHIELD", home_wording, home_terms),
            ("PA-SECURE", pa_wording, pa_terms), ("LIFE-TERM", life_wording, life_terms)]

INSURED = [
    # travel: the policy period is the trip; sum insured is the overall trip limit
    ("CS-TRV-26-002101", "TRV-GLOBE", "Aditi Rao", "2026-06-02", "2026-06-20", 1500000),
    ("CS-TRV-26-002118", "TRV-GLOBE", "Rakesh Menon", "2026-06-10", "2026-06-24", 1000000),
    ("CS-TRV-26-002125", "TRV-GLOBE", "Smita Kulkarni", "2026-07-01", "2026-07-15", 1000000),
    ("CS-TRV-26-002132", "TRV-GLOBE", "Faizal Ahmed", "2026-07-05", "2026-07-25", 1000000),
    ("CS-TRV-26-002149", "TRV-GLOBE", "Nandini Iyer", "2026-07-20", "2026-08-05", 1000000),
    ("CS-TRV-26-002156", "TRV-GLOBE", "Vivek Chandra", "2026-08-01", "2026-08-12", 1500000),
    ("CS-TRV-26-002163", "TRV-GLOBE", "Meera Pillai", "2026-08-08", "2026-08-30", 1000000),
    ("CS-TRV-26-002170", "TRV-GLOBE", "Arun Bhatia", "2026-08-15", "2026-08-28", 1000000),
    ("CS-TRV-26-002187", "TRV-GLOBE", "Sonia Dsouza", "2026-08-20", "2026-09-02", 1000000),
    ("CS-TRV-26-002194", "TRV-GLOBE", "Hemant Joshi", "2026-08-22", "2026-09-05", 1000000),
    # home: building and contents sum insured
    ("CS-HOM-26-003101", "HOME-SHIELD", "Ramesh Iyengar", "2026-04-10", "2027-04-09", 2500000),
    ("CS-HOM-26-003118", "HOME-SHIELD", "Shalini Ghosh", "2026-04-15", "2027-04-14", 1500000),
    ("CS-HOM-26-003125", "HOME-SHIELD", "Thomas Mathew", "2026-04-01", "2027-03-31", 4000000),
    ("CS-HOM-26-003132", "HOME-SHIELD", "Padma Raghavan", "2026-05-01", "2027-04-30", 2000000),
    ("CS-HOM-26-003149", "HOME-SHIELD", "Yusuf Pathan", "2026-04-20", "2027-04-19", 1800000),
    ("CS-HOM-26-003156", "HOME-SHIELD", "Kamala Devi", "2026-06-01", "2027-05-31", 2200000),
    ("CS-HOM-26-003163", "HOME-SHIELD", "Rajat Kapoor", "2026-08-01", "2027-07-31", 1000000),
    ("CS-HOM-26-003170", "HOME-SHIELD", "Gita Sharma", "2026-04-05", "2027-04-04", 1200000),
    ("CS-HOM-26-003187", "HOME-SHIELD", "Naveen Reddy", "2026-04-25", "2027-04-24", 3000000),
    ("CS-HOM-26-003194", "HOME-SHIELD", "Ananya Sen", "2026-04-01", "2026-06-30", 1500000),
    # personal accident: capital sum insured
    ("CS-PAC-26-004101", "PA-SECURE", "Sunil Shetty", "2026-04-01", "2027-03-31", 1000000),
    ("CS-PAC-26-004118", "PA-SECURE", "Rekha Nair", "2026-04-12", "2027-04-11", 500000),
    ("CS-PAC-26-004125", "PA-SECURE", "Mahesh Babu Kondapalli", "2026-04-20", "2027-04-19", 1500000),
    ("CS-PAC-26-004132", "PA-SECURE", "Zoya Mirza", "2026-05-01", "2027-04-30", 500000),
    ("CS-PAC-26-004149", "PA-SECURE", "Bharat Solanki", "2026-04-08", "2027-04-07", 700000),
    ("CS-PAC-26-004156", "PA-SECURE", "Lata Mangeshkar Joshi", "2026-05-15", "2027-05-14", 800000),
    ("CS-PAC-26-004163", "PA-SECURE", "Irfan Sheikh", "2026-04-18", "2027-04-17", 600000),
    ("CS-PAC-26-004170", "PA-SECURE", "Pallavi Deshmukh", "2026-07-20", "2027-07-19", 1000000),
    # life: sum assured; the start date is the date of commencement of risk
    ("CS-LIF-20-005101", "LIFE-TERM", "Venkatesh Subramanian", "2020-03-01", "2045-02-28", 5000000),
    ("CS-LIF-25-005118", "LIFE-TERM", "Rupa Banerjee", "2025-03-15", "2050-03-14", 3000000),
    ("CS-LIF-25-005125", "LIFE-TERM", "Kunal Malhotra", "2025-11-01", "2055-10-31", 2500000),
    ("CS-LIF-22-005132", "LIFE-TERM", "Dinesh Agarwal", "2022-02-10", "2042-02-09", 2000000),
    ("CS-LIF-21-005149", "LIFE-TERM", "Asha Verghese", "2021-06-01", "2041-05-31", 4000000),
    ("CS-LIF-16-005156", "LIFE-TERM", "Prabhakar Rao", "2016-01-15", "2026-01-14", 1500000),
    ("CS-LIF-19-005163", "LIFE-TERM", "Mohammed Rafiq", "2019-09-01", "2049-08-31", 2500000),
    ("CS-LIF-26-005170", "LIFE-TERM", "Harsha Vardhan", "2026-01-10", "2056-01-09", 1000000),  # evaluation only
]
_HOLDER = {p[0]: p[2] for p in INSURED}


# ------------------------------------------------------------- documents ---
def _doc(title: str, fields: list[tuple[str, str]], sections: list[tuple[str, str]] = ()) -> str:
    lines = [title, "SYNTHETIC DEMO DOCUMENT", ""] + [f"{k}: {v}" for k, v in fields]
    for head, text in sections:
        lines += ["", head, text]
    return "\n".join(lines) + "\n"


def _form(c: dict) -> str:
    lines = ["CLAIM FORM — Synthetic Assurance Co. Ltd. (fictional)", "SYNTHETIC DEMO DOCUMENT", "",
             f"Claim Type: {c['claim_label']}", f"Policy Number: {c['policy_number']}",
             f"Claimant Name: {c['claimant']}", f"Incident Date: {c['incident_date']}"]
    lines += [f"{k}: {v}" for k, v in c.get("form_extra", {}).items()]
    lines += [f"Claimed Amount: INR {c['form_amount']:,.2f}", "", "Description of Loss:", c["narrative"], "",
              "I declare that the information given is true and complete.", f"Signed: {c['claimant']}"]
    return "\n".join(lines) + "\n"


def _statement(title: str, c: dict, header: list[tuple[str, str]], name_label: str = "Patient/Insured Name") -> str:
    lines = [title, "SYNTHETIC DEMO DOCUMENT", ""] + [f"{k}: {v}" for k, v in header]
    lines += [f"{name_label}: {c['claimant']}", "", "Itemised Charges:"]
    for desc, amt in c["items"]:
        lines.append(f"{desc:<64} {amt:>14,.2f}")
    lines += ["", f"{'Total Amount':<64} {sum(a for _, a in c['items']):>14,.2f}"]
    return "\n".join(lines) + "\n"


def _days(d: str, n: int) -> str:
    return (date.fromisoformat(d) + timedelta(days=n)).isoformat()


def _claim(number, line, label, policy, incident, narrative, items, expected, story, age, history, files, **extra):
    claimant = extra.pop("claimant", _HOLDER[policy])
    c = dict(claim_number=number, claim_type=line, claim_label=label, policy_number=policy, claimant=claimant,
             incident_date=incident, narrative=narrative, items=items, expected=expected, story=story, age_days=age,
             history=list(history), **extra)
    c.setdefault("form_amount", sum(a for _, a in items))
    filed = REFERENCE_DAY - timedelta(days=age)
    assert date.fromisoformat(incident) < filed, f"{number}: incident {incident} is not before filing on {filed}"
    c["files"] = {"claim_form.txt": _form(c), **files(c)}
    return c


def travel_docs(c: dict, medical: bool = False, skip=(), airline: str | None = None) -> dict:
    ins = next(p for p in INSURED if p[0] == c["policy_number"])
    out = {
        "passport_copy.txt": _doc("PASSPORT COPY (DATA PAGE AND STAMPS)", [
            ("Name", c["claimant"]), ("Passport Number", f"Z{c['claim_number'][-4:]}SYN"),
            ("Exit Stamp", ins[3]), ("Entry Stamp", ins[4])]),
        "travel_ticket.txt": _doc("E-TICKET AND TRAVEL ITINERARY", [
            ("Passenger", c["claimant"]), ("Flight Number", c["flight"]), ("Destination", c["destination"]),
            ("Trip Start Date", ins[3]), ("Trip End Date", ins[4])]),
    }
    if medical:
        out["hospital_bill.txt"] = _statement("FINAL HOSPITAL BILL", c, [
            ("Hospital", c["hospital"]), ("Bill Number", f"HB-{c['claim_number'][-4:]}"),
            ("Admission Date", c["incident_date"]), ("Discharge Date", _days(c["incident_date"], c.get("stay", 2)))])
        out["discharge_summary.txt"] = _doc("DISCHARGE SUMMARY", [
            ("Hospital", c["hospital"]), ("Patient Name", c["claimant"]), ("Admission Date", c["incident_date"]),
            ("Discharge Date", _days(c["incident_date"], c.get("stay", 2))), ("Diagnosis", c["diagnosis"]),
            ("Procedure", c["procedure"])], [("Clinical Notes:", c["notes"])])
    else:
        out["claim_statement.txt"] = _statement("STATEMENT OF LOSS — TRAVEL", c, [("Destination", c["destination"])])
    if airline == "pir":
        out["airline_report.txt"] = _doc("PROPERTY IRREGULARITY REPORT", [
            ("Passenger", c["claimant"]), ("Flight Number", c["flight"]), ("Report Number", f"PIR-{c['claim_number'][-4:]}")],
            [("Findings:", "Checked bag not delivered; trace closed after 21 days and the bag declared lost by the airline.")])
    elif airline == "delay":
        out["airline_report.txt"] = _doc("FLIGHT DELAY CERTIFICATE", [
            ("Passenger", c["claimant"]), ("Flight Number", c["flight"]), ("Scheduled Departure", c["incident_date"])],
            [("Findings:", c["delay_note"])])
    for name in skip:
        out.pop(name)
    return out


def T(number, policy, incident, narrative, items, expected, story, age, history=(), destination="Singapore",
      flight="SQ-SYN-0502", medical=False, airline=None, skip=(), **extra):
    return _claim(number, "travel", "Travel", policy, incident, narrative, items, expected, story, age, history,
                  lambda c: travel_docs(c, medical, skip, airline), destination=destination, flight=flight, **extra)


def home_docs(c: dict, skip=(), fir: str | None = None) -> dict:
    out = {
        "claim_statement.txt": _statement("STATEMENT OF LOSS — HOME", c, [("Property Address", c["address"])]),
        "survey_report.txt": _doc("SURVEY REPORT", [
            ("Surveyor", "Coastal Loss Assessors (fictional)"), ("Property Address", c["address"]),
            ("Value at Risk", f"INR {c['value_at_risk']:,.2f}"), ("Cause of Loss", c["cause"])],
            [("Surveyor Findings:", c["survey"])]),
    }
    if fir:
        out["police_report.txt"] = _doc("POLICE REPORT (FIR COPY)", [
            ("FIR Number", f"FIR-SYN-{c['claim_number'][-4:]}"), ("Date of Incident", c["incident_date"]),
            ("Property Address", c["address"])], [("Findings:", fir)])
    for name in skip:
        out.pop(name)
    return out


def P(number, policy, incident, narrative, items, expected, story, age, cause, survey, value_at_risk, history=(),
      address="Flat 4B, Synthetic Residency, Bengaluru", fir=None, skip=(), **extra):
    return _claim(number, "home", "Home", policy, incident, narrative, items, expected, story, age, history,
                  lambda c: home_docs(c, skip, fir), address=address, cause=cause, survey=survey,
                  value_at_risk=value_at_risk, form_extra={"Property Address": address}, **extra)


def pa_docs(c: dict, skip=(), fir: str | None = None) -> dict:
    out = {
        "claim_statement.txt": _statement("BENEFIT CLAIM STATEMENT — PERSONAL ACCIDENT", c, []),
        "medical_certificate.txt": _doc("MEDICAL CERTIFICATE (TREATING DOCTOR)", [
            ("Patient Name", c["claimant"]), ("Doctor", "Dr. S. Synthetic, Orthopaedics (fictional)"),
            ("Nature of Injury", c["injury"])], [("Clinical Notes:", c["notes"])]),
    }
    if fir:
        out["police_report.txt"] = _doc("POLICE REPORT (FIR COPY)", [
            ("FIR Number", f"FIR-SYN-{c['claim_number'][-4:]}"), ("Date of Accident", c["incident_date"])],
            [("Findings:", fir)])
    for name in skip:
        out.pop(name)
    return out


def A(number, policy, incident, narrative, items, expected, story, age, injury, notes, history=(), fir=None, skip=(),
      **extra):
    return _claim(number, "personal_accident", "Personal Accident", policy, incident, narrative, items, expected, story,
                  age, history, lambda c: pa_docs(c, skip, fir), injury=injury, notes=notes, **extra)


def life_docs(c: dict, skip=()) -> dict:
    out = {
        "claim_statement.txt": _statement("BENEFIT CLAIM STATEMENT — LIFE", c, [("Deceased Name", c["deceased"])],
                                          "Claimant Name"),
        "death_certificate.txt": _doc("DEATH CERTIFICATE", [
            ("Deceased Name", c["deceased"]), ("Date of Death", c["incident_date"]),
            ("Place of Death", c["place"]), ("Registration Number", f"DC-SYN-{c['claim_number'][-4:]}")]),
        "medical_certificate.txt": _doc("MEDICAL ATTENDANT'S CERTIFICATE", [
            ("Deceased Name", c["deceased"]), ("Cause of Death", c["cause_of_death"]),
            ("Doctor", "Dr. R. Synthetic, General Medicine (fictional)")], [("Clinical Notes:", c["notes"])]),
    }
    for name in skip:
        out.pop(name)
    return out


def L(number, policy, incident, nominee, narrative, cause_of_death, notes, expected, story, age, history=(),
      place="City General Hospital (fictional)", skip=(), **extra):
    ins = next(p for p in INSURED if p[0] == policy)
    items = [("Death Benefit - Sum Assured", ins[5])]
    # the claimant on a death claim is the nominee; the policy holder is the deceased life assured
    c = _claim(number, "life", "Life", policy, incident, narrative, items, expected, story, age, history,
               lambda c: life_docs(c, skip), claimant=nominee, deceased=ins[2], cause_of_death=cause_of_death, notes=notes, place=place,
               form_extra={"Deceased Name": ins[2], "Nominee Name": nominee}, **extra)
    return c


def _act(action: str, after: int, role: str = "adjuster", notes: str = "", payable_delta: int | None = None) -> dict:
    return {"action": action, "after_days": after, "actor": role, "notes": notes, "payable_delta": payable_delta}


# ---------------------------------------------------------------- claims ---
def demo_claims() -> list[dict]:
    B = []
    # ---- travel
    B.append(T("CLM-T-4101", "CS-TRV-26-002101", "2026-06-08",
               "Severe abdominal pain on the fourth day of the trip; admitted in Singapore and operated for appendicitis.",
               [("Room Charges - Semi Private (2 days @ 38,000)", 76000), ("Surgeon and Anaesthetist Fees", 145000),
                ("Operation Theatre Charges", 62000), ("Pharmacy - Medicines and Drugs", 21000),
                ("Laboratory Tests and CT Abdomen", 28000), ("Registration Charges", 4000)],
               "PARTIAL_APPROVAL", "Emergency surgery abroad: registration charges not payable and the medical deductible applies",
               60, [_act("ESCALATE", 2, notes="Payable is above my approval limit."),
                    _act("APPROVE", 5, role="supervisor", notes="Emergency admission confirmed with the hospital.")],
               medical=True, hospital="Marina Bay General Hospital (fictional)", diagnosis="Acute appendicitis",
               procedure="Laparoscopic appendicectomy", notes="Uneventful recovery; fit to fly after 5 days.", stay=2))
    B.append(T("CLM-T-4102", "CS-TRV-26-002118", "2026-06-10",
               "Checked bag did not arrive in Dubai and the airline later declared it lost.",
               [("Checked baggage - laptop", 85000), ("Checked baggage - clothes and shoes", 22000),
                ("Checked baggage - camera", 32000)],
               "PARTIAL_APPROVAL", "Lost baggage: 10% depreciation, the INR 15,000 per-item limit and the INR 50,000 trip limit",
               55, [_act("APPROVE", 7, notes="Airline PIR and trace closure on file.")], destination="Dubai",
               flight="EK-SYN-0511", airline="pir"))
    B.append(T("CLM-T-4103", "CS-TRV-26-002125", "2026-07-14",
               "Return flight from Frankfurt delayed by 16 hours; stayed overnight at an airport hotel.",
               [("Trip delay - airport hotel for one night", 11500), ("Trip delay - meals and local transport", 3000)],
               "PARTIAL_APPROVAL", "Trip delay above the INR 10,000 limit", 45,
               [_act("APPROVE", 3)], destination="Frankfurt", flight="LH-SYN-0761", airline="delay",
               delay_note="Flight delayed 16 hours owing to an aircraft technical fault. Passengers were not accommodated by the airline."))
    B.append(T("CLM-T-4104", "CS-TRV-26-002132", "2026-07-06",
               "Trip cut short after the insured's father was hospitalised in Chennai; prepaid bookings could not be refunded.",
               [("Trip cancellation - non-refundable hotel booking", 42000), ("Trip cancellation - change fee on return flight", 18000)],
               "APPROVE", "Trip cancellation within the INR 1,00,000 limit: paid in full", 50,
               [_act("APPROVE", 6, notes="Hospital certificate for the father on file.")], destination="Paris",
               flight="AF-SYN-0218"))
    B.append(T("CLM-T-4105", "CS-TRV-26-002149", "2026-07-26",
               "Ear injury while scuba diving on a reef dive in Bali; treated at a local clinic.",
               [("Room Charges - Clinic (1 day @ 18,000)", 18000), ("Consultant Physician Fees", 12000),
                ("Pharmacy - Medicines and Drugs", 4500)],
               "RECOMMEND_REJECT", "Scuba diving is a hazardous activity excluded under clause 3.3", 38,
               [_act("REJECT", 4, notes="Dive centre record confirms a recreational scuba dive; exclusion 3.3 applies.")],
               medical=True, destination="Bali", flight="GA-SYN-0881", hospital="Kuta Island Clinic (fictional)",
               diagnosis="Barotrauma of the right ear after scuba diving", procedure="Medical management",
               notes="Advised no diving or flying for 72 hours.", stay=1))
    B.append(T("CLM-T-4106", "CS-TRV-26-002156", "2026-08-05",
               "Chest pain while sightseeing in London; admitted for observation and angiography.",
               [("ICU Charges (2 days @ 95,000)", 190000), ("Cardiologist Fees", 120000), ("Cath Lab Charges", 180000),
                ("Pharmacy - Medicines and Drugs", 35000)],
               "RECOMMEND_REJECT", "Known heart patient: pre-existing condition excluded under clause 3.2", 32,
               medical=True, destination="London", flight="BA-SYN-0118", hospital="Thames Heart Centre (fictional)",
               diagnosis="Unstable angina in a known case of coronary artery disease", procedure="Coronary angiography",
               notes="Known case of coronary artery disease since 2019 on regular medication.", stay=3))
    B.append(T("CLM-T-4107", "CS-TRV-26-002163", "2026-08-18",
               "Passport stolen from a hotel room in Rome; emergency certificate issued by the embassy.",
               [("Passport replacement - emergency certificate and photographs", 9800)],
               "APPROVE", "Loss of passport within the INR 15,000 limit", 20, destination="Rome", flight="AZ-SYN-0769"))
    B.append(T("CLM-T-4108", "CS-TRV-26-002170", "2026-08-22",
               "Fell on a wet hotel staircase in Bangkok and fractured the wrist.",
               [("Room Charges - Ward (1 day @ 14,000)", 14000), ("Orthopaedic Surgeon Fees", 26000),
                ("X-Ray and Diagnostics", 6500), ("Pharmacy - Medicines and Drugs", 3500)],
               "REQUEST_INFO", "Passport copy not submitted, so the trip dates cannot be confirmed", 12,
               [_act("REQUEST_INFO", 2, notes="Asked for the passport copy with entry and exit stamps.")],
               medical=True, destination="Bangkok", flight="TG-SYN-0316", hospital="Riverside Bangkok Hospital (fictional)",
               diagnosis="Fracture of the left distal radius after a fall", procedure="Closed reduction and cast",
               notes="Cast for six weeks; review in India.", stay=1, skip=("passport_copy.txt",)))
    B.append(T("CLM-T-4109", "CS-TRV-26-002187", "2026-09-06",
               "Fever and vomiting after returning home; treated as an outpatient.",
               [("Consultant Physician Fees", 3500), ("Laboratory Tests - Blood Panel", 4800),
                ("Pharmacy - Medicines and Drugs", 2200)],
               "RECOMMEND_REJECT", "Illness began after the trip ended on 2026-09-02, outside the period of cover", 22,
               [_act("REJECT", 3, notes="Treatment was in India after the trip; outside the policy period.")],
               medical=True, destination="Kuala Lumpur", flight="MH-SYN-0193", hospital="Home Town Clinic (fictional)",
               diagnosis="Acute gastroenteritis", procedure="Outpatient treatment", notes="Symptoms began on 2026-09-05.",
               stay=0))
    B.append(T("CLM-T-4110", "CS-TRV-26-002194", "2026-08-29",
               "Collapsed in New York; ICU care and an air ambulance back to Mumbai.",
               [("ICU Charges (4 days @ 1,20,000)", 480000), ("Physician and Specialist Fees", 160000),
                ("Pharmacy - Medicines and Drugs", 70000), ("Medical evacuation - air ambulance to Mumbai", 240000)],
               "INVESTIGATE", "High risk: 95% of the trip sum insured and a claim form that does not match the bills", 8,
               medical=True, destination="New York", flight="AI-SYN-0101", hospital="Hudson Medical Center (fictional)",
               diagnosis="Acute pancreatitis", procedure="ICU management", notes="Stabilised and evacuated on day 4.",
               stay=4, form_amount=1250000))
    # ---- home
    B.append(P("CLM-P-5101", "CS-HOM-26-003101", "2026-08-02",
               "Fire in the kitchen from an overheated cooking gas cylinder damaged the kitchen and dining area.",
               [("Kitchen wall, ceiling and wiring repair (building)", 185000), ("Refrigerator (appliance)", 42000),
                ("Dining table and chairs (furniture)", 60000)],
               "PARTIAL_APPROVAL", "Kitchen fire: depreciation on contents and the deductible", 58,
               "Fire", "Fire started at the gas stove; kitchen walls and false ceiling charred. Loss assessed at the replacement and repair costs claimed.",
               2400000, [_act("ESCALATE", 4, notes="Payable is above my approval limit."),
                         _act("APPROVE", 9, role="supervisor", notes="Survey report supports the assessed loss.")]))
    B.append(P("CLM-P-5102", "CS-HOM-26-003118", "2026-07-19",
               "House broken into while the family was at a wedding for the evening; television, laptop and jewellery taken.",
               [("LED television 55 inch (electronics)", 75000), ("Laptop (electronics)", 90000),
                ("Gold jewellery from the locked almirah safe", 240000)],
               "PARTIAL_APPROVAL", "Burglary: jewellery above the INR 1,00,000 limit and depreciation on electronics", 47,
               "Burglary", "Main door lock broken; locked safe forced open. Police visited the same night.",
               1400000, [_act("ESCALATE", 3, notes="Above my approval limit."),
                         _act("APPROVE", 8, role="supervisor", notes="FIR and bills verified.")],
               address="12 Synthetic Lane, Kolkata", fir="Burglary reported at 23:40. Lock broken; jewellery and electronics stolen."))
    B.append(P("CLM-P-5103", "CS-HOM-26-003125", "2026-08-30",
               "Flood water entered the ground floor after two days of heavy rain; the family moved out for repairs.",
               [("Ground floor flooring, plaster and doors repair (building)", 320000), ("Sofa and beds (furniture)", 80000),
                ("Debris removal and cleaning", 65000), ("Alternative accommodation rent for 3 months", 90000)],
               "PARTIAL_APPROVAL", "Flood: under-insured by a third, so the average clause applies, with debris and rent sub-limits",
               25, "Flood", "Water level reached 1.2 metres inside the house. The surveyor values the house and contents at INR 60,00,000 against a sum insured of INR 40,00,000.",
               6000000, address="Plot 7, Synthetic Nagar, Chennai"))
    B.append(P("CLM-P-5104", "CS-HOM-26-003132", "2026-07-28",
               "Damp patches and peeling plaster in two bedrooms; the bathroom pipe had been leaking for months.",
               [("Bedroom walls replaster and repaint (building)", 95000)],
               "RECOMMEND_REJECT", "Gradual seepage is excluded under clause 3.2", 40,
               "Seepage", "Long-standing seepage from a concealed bathroom pipe; gradual deterioration, not a sudden event.",
               2500000, [_act("REJECT", 5, notes="Surveyor confirms gradual seepage; exclusion 3.2.")]))
    B.append(P("CLM-P-5105", "CS-HOM-26-003149", "2026-06-25",
               "Burglary discovered on returning from a two-month stay abroad.",
               [("Television (electronics)", 60000), ("Washing machine (appliance)", 38000)],
               "RECOMMEND_REJECT", "House unoccupied for more than 30 days: excluded under clause 3.3", 52,
               "Burglary", "Neighbours confirm the house was unoccupied for about 60 days before the break-in.",
               1600000, [_act("REJECT", 6, notes="House unoccupied for about 60 days; clause 3.3.")],
               address="44 Synthetic Road, Ahmedabad",
               fir="House found broken into on return; occupants away since late April."))
    B.append(P("CLM-P-5106", "CS-HOM-26-003156", "2026-09-14",
               "Storm blew off part of the roof sheets and damaged the terrace water tank.",
               [("Roof sheets and terrace tank replacement (building)", 68000)],
               "REQUEST_INFO", "Survey report not yet received", 9,
               "Storm", "Pending", 2400000, skip=("survey_report.txt",), address="Synthetic Farmhouse, Nashik"))
    B.append(P("CLM-P-5107", "CS-HOM-26-003163", "2026-08-18",
               "Fire spread from a neighbouring shop and gutted the house.",
               [("Structure rebuilding (building)", 720000), ("Furniture (furniture)", 120000), ("Electronics (electronics)", 90000)],
               "INVESTIGATE", "High risk: 93% of the sum insured, 17 days after cover began", 30,
               "Fire", "Extensive fire damage; origin under police investigation.", 1000000,
               address="Shop Lane, Synthetic Market, Jaipur"))
    B.append(P("CLM-P-5108", "CS-HOM-26-003170", "2026-08-25",
               "Lightning strike caused a power surge that burnt out the television and the router.",
               [("LED television (electronics)", 52000), ("Wi-Fi router (electronics)", 6000)],
               "PARTIAL_APPROVAL", "Lightning surge: electronics depreciation and the deductible", 19,
               "Lightning", "Surge damage confirmed by the service centre report.", 1100000,
               [_act("APPROVE", 4)], address="9 Synthetic Colony, Pune"))
    B.append(P("CLM-P-5109", "CS-HOM-26-003187", "2026-09-20",
               "Water pipe burst in the loft flooded the bedroom; wardrobe clothes and the mattress ruined.",
               [("Clothes in the wardrobe (clothing)", 48000), ("Mattress and bed (furniture)", 36000),
                ("Bedroom ceiling repair (building)", 30000)],
               "PARTIAL_APPROVAL", "Sudden pipe burst: clothing and furniture depreciation and the deductible", 6,
               "Inundation", "Sudden burst of the loft supply pipe; no sign of earlier leakage.", 2800000,
               address="Tower C, Synthetic Heights, Hyderabad"))
    B.append(P("CLM-P-5110", "CS-HOM-26-003194", "2026-07-12",
               "Short circuit fire in the living room.",
               [("Sofa set (furniture)", 70000), ("Television (electronics)", 45000)],
               "RECOMMEND_REJECT", "Fire on 2026-07-12, after the policy expired on 2026-06-30", 44,
               "Fire", "Short circuit at the television socket.", 1500000,
               [_act("REJECT", 3, notes="Policy expired on 2026-06-30 and was not renewed.")],
               address="21 Synthetic Street, Kochi"))
    # ---- personal accident
    B.append(A("CLM-A-6101", "CS-PAC-26-004101", "2026-07-30",
               "Slipped on a wet staircase at the office and fractured the right ankle.",
               [("Temporary total disablement - 6 weeks", 72000), ("Accident medical expenses - surgery and physiotherapy", 45000)],
               "PARTIAL_APPROVAL", "Weekly benefit limited to INR 10,000 a week; medical expenses paid in full", 54,
               "Fracture of the right ankle after a fall", "Plaster cast and screws; unable to work for six weeks.",
               [_act("APPROVE", 6, notes="Leave certificate from the employer on file.")]))
    B.append(A("CLM-A-6102", "CS-PAC-26-004118", "2026-07-08",
               "Right index finger crushed in a press machine accident at the workshop.",
               [("Permanent partial disablement - loss of right index finger", 75000),
                ("Temporary total disablement - 4 weeks", 20000)],
               "PARTIAL_APPROVAL", "Index finger is 10% of the sum insured under the disablement table", 46,
               "Traumatic amputation of the right index finger", "Finger amputated at the base; stump healed.",
               [_act("APPROVE", 7, notes="Disability certificate confirms the loss of the index finger.")]))
    B.append(A("CLM-A-6103", "CS-PAC-26-004125", "2026-08-12",
               "Killed in a road accident when a truck hit the insured's motorcycle on the highway.",
               [("Accidental death benefit", 1500000)],
               "APPROVE", "Accidental death: 100% of the capital sum insured to the nominee", 36,
               "Fatal head injury in a road traffic accident", "Declared dead on arrival at the trauma centre.",
               [_act("ESCALATE", 2, notes="Above my approval limit; death claim for supervisor."),
                _act("APPROVE", 6, role="supervisor", notes="FIR and post-mortem report on file.")],
               fir="Truck hit the motorcycle from behind on the highway. Truck driver arrested."))
    B.append(A("CLM-A-6104", "CS-PAC-26-004132", "2026-08-20",
               "Hospitalised with dengue fever and unable to work for three weeks.",
               [("Temporary total disablement - 3 weeks", 15000)],
               "RECOMMEND_REJECT", "Dengue is an illness, not an accident (clause 1.3)", 28,
               "Dengue fever with low platelets", "Viral fever; treated with IV fluids.",
               [_act("REJECT", 3, notes="Illness, not an accidental injury.")]))
    B.append(A("CLM-A-6105", "CS-PAC-26-004149", "2026-08-03",
               "Injured when the insured's car hit a divider late at night.",
               [("Temporary total disablement - 8 weeks", 56000), ("Accident medical expenses - hospital treatment", 38000)],
               "RECOMMEND_REJECT", "Driving under the influence of alcohol: excluded under clause 3.2", 42,
               "Fracture of both forearm bones in a road accident", "Blood alcohol well above the legal limit on admission.",
               [_act("REJECT", 5, notes="Police report and blood test show the insured was drunk.")],
               fir="Single-vehicle accident. Driver was under the influence of alcohol."))
    B.append(A("CLM-A-6106", "CS-PAC-26-004156", "2026-06-24",
               "Left foot crushed under a falling steel beam at a construction site; amputated below the ankle.",
               [("Permanent partial disablement - loss of one foot", 400000)],
               "APPROVE", "Loss of one foot is 50% of the sum insured", 64,
               "Traumatic amputation of the left foot", "Below-ankle amputation; using a prosthesis.",
               [_act("ESCALATE", 3, notes="Above my approval limit."),
                _act("APPROVE", 10, role="supervisor", notes="Medical board certificate confirms the loss of one foot.")]))
    B.append(A("CLM-A-6107", "CS-PAC-26-004163", "2026-09-12",
               "Fell from a ladder while repairing the roof and fractured the left wrist.",
               [("Temporary total disablement - 5 weeks", 30000)],
               "REQUEST_INFO", "Doctor's certificate not submitted", 11,
               "Fracture of the left wrist after a fall", "Cast applied.", skip=("medical_certificate.txt",)))
    B.append(A("CLM-A-6108", "CS-PAC-26-004170", "2026-09-04",
               "Spinal cord injury in a fall from a balcony; paralysed below the waist.",
               [("Permanent total disablement - paraplegia", 1000000)],
               "INVESTIGATE", "High risk: full sum insured claimed 46 days after cover began", 15,
               "Spinal cord injury with paraplegia after a fall", "Complete loss of use of both legs."))
    # ---- life
    B.append(L("CLM-L-7101", "CS-LIF-20-005101", "2026-07-21", "Lalitha Venkatesh",
               "The life assured died of a heart attack at home.", "Acute myocardial infarction",
               "Known hypertensive for eight years; collapsed at home and was declared dead on arrival.",
               "APPROVE", "Death six years into the policy: sum assured paid in full", 56,
               [_act("ESCALATE", 2, notes="Death claim above my approval limit."),
                _act("APPROVE", 9, role="supervisor", notes="All documents in order; outside the section 45 period.")]))
    B.append(L("CLM-L-7102", "CS-LIF-25-005118", "2026-08-28", "Sourav Banerjee",
               "The life assured died of advanced stomach cancer.", "Carcinoma of the stomach with metastases",
               "Diagnosed in July 2026; hospital records mention symptoms for two years before the policy began.",
               "INVESTIGATE", "Death 17 months into the policy: inside the section 45 period, so it is investigated", 30,
               [_act("INVESTIGATE", 3, notes="Records suggest symptoms before the proposal; checking for non-disclosure.")]))
    B.append(L("CLM-L-7103", "CS-LIF-25-005125", "2026-07-02", "Neha Malhotra",
               "The life assured was found dead at home.", "Suicide by hanging",
               "Inquest concluded suicide.",
               "RECOMMEND_REJECT", "Suicide eight months after commencement: excluded under clause 3.1", 40,
               [_act("REJECT", 5, notes="Suicide within 12 months; premium refund handled by servicing.")]))
    B.append(L("CLM-L-7104", "CS-LIF-22-005132", "2026-09-10", "Sarita Agarwal",
               "The life assured died after a long illness.", "Suicide during severe depression",
               "Treated for depression since 2025.",
               "APPROVE", "Suicide 55 months after commencement: the 12-month exclusion no longer applies", 14))
    B.append(L("CLM-L-7105", "CS-LIF-21-005149", "2026-09-18", "Joseph Verghese",
               "The life assured died in hospital after a stroke.", "Intracerebral haemorrhage",
               "Admitted unconscious; died on day three.",
               "REQUEST_INFO", "Death certificate not submitted", 7, skip=("death_certificate.txt",)))
    B.append(L("CLM-L-7106", "CS-LIF-16-005156", "2026-05-20", "Kamala Rao",
               "The life assured died of kidney failure.", "End-stage renal disease",
               "On dialysis for one year.",
               "RECOMMEND_REJECT", "Death on 2026-05-20, after the ten-year term ended on 2026-01-14", 48,
               [_act("REJECT", 4, notes="Term policy matured without value on 2026-01-14.")]))
    B.append(L("CLM-L-7107", "CS-LIF-19-005163", "2026-09-03", "Shabana Rafiq",
               "The life assured died in a road accident while travelling by bus.", "Multiple injuries in a road traffic accident",
               "Bus overturned on the highway; declared dead at the scene.",
               "APPROVE", "Accidental death seven years into the policy: sum assured paid in full", 19,
               [_act("ESCALATE", 2, notes="Death claim above my approval limit.")]))
    return B


def eval_claims() -> list[dict]:
    """Packets for the golden evaluation (never seeded); expected amounts are worked by hand in golden_cases.json."""
    E = []
    E.append(T("EVAL-T-01", "CS-TRV-26-002101", "2026-06-12",
               "Lost checked bag and a 14-hour flight delay on the way back from Singapore.",
               [("Checked baggage - suitcase and clothes", 40000), ("Checked baggage - tablet", 12000),
                ("Trip delay - hotel and meals", 12500)],
               "PARTIAL_APPROVAL", "evaluation", 10, airline="pir"))
    E.append(P("EVAL-P-01", "CS-HOM-26-003101", "2026-09-01",
               "Burglary at night; television and jewellery stolen.",
               [("Television (electronics)", 80000), ("Gold bangles (jewellery)", 150000)],
               "PARTIAL_APPROVAL", "evaluation", 10, "Burglary",
               "Window grill cut; locked safe forced open. Value at risk confirmed at INR 50,00,000.", 5000000,
               fir="Burglary reported the same night."))
    E.append(A("EVAL-A-01", "CS-PAC-26-004118", "2026-09-05",
               "Thumb lost in a kitchen accident with a food processor blade.",
               [("Permanent partial disablement - loss of left thumb", 100000), ("Temporary total disablement - 3 weeks", 18000),
                ("Accident medical expenses - surgery", 60000)],
               "APPROVE", "evaluation", 10, "Traumatic amputation of the left thumb", "Thumb amputated at the base."))
    E.append(L("EVAL-L-01", "CS-LIF-26-005170", "2026-08-15", "Kavya Vardhan",
               "The life assured died by suicide.", "Suicide",
               "Inquest concluded suicide.", "RECOMMEND_REJECT", "evaluation", 10))
    return E
