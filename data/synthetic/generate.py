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
  data/claims/demo_book/<CLAIM>/*.txt, demo_book.json  a larger demo book of business (42 claims, seeded)
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


INSURED = [
    # policy_number, product, holder, start, end, sum insured
    ("CS-HLT-24-000117", "HLT-SHIELD", "Ravi Kumar", "2024-06-01", "2026-05-31", 500000),
    ("CS-HLT-25-000342", "HLT-SHIELD", "Meena Iyer", "2025-02-10", "2026-02-09", 300000),
    ("CS-HLT-25-000518", "HLT-SHIELD", "Arjun Mehta", "2025-05-01", "2026-04-30", 500000),
    ("CS-HLT-23-000089", "HLT-SHIELD", "Fatima Shaikh", "2023-09-15", "2026-09-14", 400000),
    ("CS-HLT-24-000233", "HLT-SHIELD", "Suresh Nair", "2024-01-20", "2026-01-19", 300000),
    ("CS-MTR-25-001204", "MTR-SECURE", "Priya Sharma", "2025-04-15", "2026-04-14", 650000),
    ("CS-MTR-25-001377", "MTR-SECURE", "Karthik Rao", "2025-06-01", "2026-05-31", 480000),
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
        if c["claim_type"] == "health":
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


# ------------------------------------------------------------ demo book ---
# A larger synthetic book of business so the dashboard, queues and claims list have something to show.
# Each claim is designed to reach one outcome through the policy rules (the expected recommendation is
# checked by backend/tests/test_demo_book.py). age_days spreads filing dates over the eight weeks before
# seeding; history lists reviewer actions the seeder replays as labelled demo history.
DEMO_INSURED = [
    ("CS-HLT-24-000611", "HLT-SHIELD", "Anil Deshpande", "2024-03-01", "2026-02-28", 500000),
    ("CS-HLT-23-000624", "HLT-SHIELD", "Lakshmi Venkatesh", "2023-07-01", "2026-06-30", 500000),
    ("CS-HLT-22-000637", "HLT-SHIELD", "Rohan Kapoor", "2022-12-01", "2026-11-30", 1000000),
    ("CS-HLT-24-000648", "HLT-SHIELD", "Neha Joshi", "2024-05-15", "2026-05-14", 300000),
    ("CS-HLT-23-000655", "HLT-SHIELD", "Imran Qureshi", "2023-04-10", "2026-04-09", 500000),
    ("CS-HLT-22-000662", "HLT-SHIELD", "Deepa Menon", "2022-06-01", "2026-05-31", 500000),
    ("CS-HLT-25-000679", "HLT-SHIELD", "Vikram Singh", "2025-09-10", "2026-09-09", 500000),
    ("CS-HLT-24-000686", "HLT-SHIELD", "Geeta Pillai", "2024-02-01", "2026-01-31", 300000),
    ("CS-HLT-23-000693", "HLT-SHIELD", "Sanjay Gupta", "2023-10-01", "2026-09-30", 500000),
    ("CS-HLT-24-000707", "HLT-SHIELD", "Ayesha Khan", "2024-08-01", "2026-07-31", 500000),
    ("CS-HLT-22-000714", "HLT-SHIELD", "Kavitha Rao", "2022-03-15", "2026-03-14", 1000000),
    ("CS-HLT-25-000721", "HLT-SHIELD", "Harish Patel", "2025-07-01", "2026-06-30", 300000),
    ("CS-HLT-24-000738", "HLT-SHIELD", "Sunita Reddy", "2024-11-05", "2026-11-04", 300000),
    ("CS-HLT-25-000745", "HLT-SHIELD", "Manoj Tiwari", "2025-01-20", "2026-01-19", 300000),
    ("CS-HLT-25-000752", "HLT-SHIELD", "Pooja Bansal", "2025-10-01", "2026-09-30", 500000),
    ("CS-HLT-23-000769", "HLT-SHIELD", "Nikhil Arora", "2023-05-01", "2026-04-30", 500000),
    ("CS-HLT-24-000776", "HLT-SHIELD", "Shreya Kulkarni", "2024-04-01", "2026-03-31", 500000),
    ("CS-HLT-24-000783", "HLT-SHIELD", "Rahul Saxena", "2024-10-01", "2025-09-30", 300000),
    ("CS-HLT-23-000790", "HLT-SHIELD", "Prakash Yadav", "2023-08-01", "2026-07-31", 500000),
    ("CS-HLT-24-000805", "HLT-SHIELD", "Farhan Ali", "2024-06-10", "2026-06-09", 500000),
    ("CS-HLT-23-000812", "HLT-SHIELD", "Leela Thomas", "2023-02-01", "2026-01-31", 300000),
    ("CS-HLT-24-000829", "HLT-SHIELD", "Mohan Das", "2024-09-01", "2026-08-31", 500000),
    ("CS-HLT-25-000836", "HLT-SHIELD", "Ritu Malhotra", "2025-08-01", "2026-07-31", 300000),
    ("CS-HLT-25-000843", "HLT-SHIELD", "Ajay Chauhan", "2025-07-15", "2026-07-14", 300000),
    ("CS-MTR-25-001411", "MTR-SECURE", "Anjali Desai", "2025-05-01", "2026-04-30", 720000),
    ("CS-MTR-25-001428", "MTR-SECURE", "Rajiv Menon", "2025-04-20", "2026-04-19", 1100000),
    ("CS-MTR-25-001435", "MTR-SECURE", "Swati Nair", "2025-04-05", "2026-04-04", 560000),
    ("CS-MTR-25-001442", "MTR-SECURE", "Gopal Krishnan", "2025-06-01", "2026-05-31", 260000),
    ("CS-MTR-25-001459", "MTR-SECURE", "Tanvi Shah", "2025-04-12", "2026-04-11", 95000),
    ("CS-MTR-25-001466", "MTR-SECURE", "Arvind Bhat", "2025-05-20", "2026-05-19", 900000),
    ("CS-MTR-25-001473", "MTR-SECURE", "Divya Hegde", "2025-07-10", "2026-07-09", 640000),
    ("CS-MTR-25-001480", "MTR-SECURE", "Kiran Kumar", "2025-04-25", "2026-04-24", 480000),
    ("CS-MTR-25-001497", "MTR-SECURE", "Varun Malhotra", "2025-04-01", "2026-03-31", 700000),
    ("CS-MTR-25-001503", "MTR-SECURE", "Sneha Iyer", "2025-06-15", "2026-06-14", 520000),
    ("CS-MTR-25-001510", "MTR-SECURE", "Pranav Kulkarni", "2025-04-18", "2026-04-17", 610000),
    ("CS-MTR-25-001527", "MTR-SECURE", "Nisha Agarwal", "2025-04-02", "2026-04-01", 830000),
    ("CS-MTR-25-001534", "MTR-SECURE", "Sameer Joshi", "2025-09-01", "2026-08-31", 450000),
    ("CS-MTR-25-001541", "MTR-SECURE", "Alok Verma", "2025-05-05", "2026-05-04", 500000),
    ("CS-MTR-25-001558", "MTR-SECURE", "Bhavna Shetty", "2025-04-28", "2026-04-27", 540000),
    ("CS-MTR-25-001565", "MTR-SECURE", "Jatin Sethi", "2025-11-01", "2026-10-31", 400000),
    ("CS-MTR-25-001572", "MTR-SECURE", "Ishaan Bose", "2025-08-20", "2026-08-19", 300000),
]
_HOLDER = {p[0]: p[2] for p in DEMO_INSURED}


def _act(action: str, after: int, role: str = "adjuster", notes: str = "", payable_delta: int | None = None) -> dict:
    return {"action": action, "after_days": after, "actor": role, "notes": notes, "payable_delta": payable_delta}


def H(number, policy, incident, hospital, narrative, diagnosis, procedure, items, days, expected, story, age, history=(),
      notes="Recovered and discharged in stable condition.", **extra) -> dict:
    disch = (date.fromisoformat(incident) + timedelta(days=days)).isoformat()
    return dict(claim_number=number, claim_type="health", policy_number=policy, claimant=_HOLDER[policy],
                incident_date=incident, hospital=f"{hospital} (fictional)", narrative=narrative, items=items,
                admit=incident, disch=disch, diagnosis=diagnosis, procedure=procedure, notes=notes,
                expected=expected, story=story, age_days=age, history=list(history), **extra)


def M(number, policy, incident, vehicle, cc, first_reg, reg_no, narrative, items, expected, story, age, history=(),
      police="Collision confirmed. No injuries reported.", **extra) -> dict:
    return dict(claim_number=number, claim_type="motor", policy_number=policy, claimant=_HOLDER[policy],
                incident_date=incident, fir=f"FIR-SYN-{number[-4:]}",
                form_extra={"Vehicle Registration": reg_no, "Vehicle Make and Model": vehicle,
                            "Date of First Registration": first_reg, "Engine Capacity cc": str(cc)},
                narrative=narrative, items=items, police=police, expected=expected, story=story, age_days=age,
                history=list(history), **extra)


def demo_book() -> list[dict]:
    room = "Room Rent - Twin Sharing"
    B = []
    # ---- health: covered, paid after the policy's deductions
    B.append(H("CLM-H-1101", "CS-HLT-24-000611", "2025-10-14", "Lakeview Multispeciality Hospital",
               "High fever for a week with abdominal pain; admitted and treated for typhoid fever.",
               "Typhoid fever", "Medical management with IV antibiotics",
               [(f"{room} (4 days @ 5,500)", 22000), ("Consultant Physician Fees", 9500),
                ("Pharmacy - Medicines and Drugs", 11800), ("Laboratory Tests - Widal and Blood Culture", 4200),
                ("Consumables - Gloves, Masks, Admission Kit", 1600)], 4,
               "PARTIAL_APPROVAL", "Room rent above the daily cap, consumables excluded, deductible and co-pay", 41,
               [_act("APPROVE", 6, notes="Bill matches the discharge summary.")]))
    B.append(H("CLM-H-1102", "CS-HLT-23-000624", "2025-11-20", "Greenfield General Hospital",
               "Recurrent pain in the upper right abdomen; gallstones found on ultrasound and operated.",
               "Cholelithiasis with chronic cholecystitis", "Laparoscopic cholecystectomy",
               [("Room Rent - Single Private (3 days @ 7,000)", 21000), ("Surgeon Fees", 42000),
                ("Operation Theatre Charges", 16000), ("Pharmacy - Medicines and Drugs", 9800),
                ("Laboratory Tests and Ultrasound", 6500), ("Consumables - Surgical Kit", 2900)], 3,
               "PARTIAL_APPROVAL", "Planned surgery in a private room above the room-rent cap", 33,
               [_act("APPROVE", 9, notes="Operative notes support the procedure.")]))
    B.append(H("CLM-H-1103", "CS-HLT-22-000637", "2026-01-08", "Sunrise Care Hospital",
               "Chest pain on exertion; coronary angiography showed a blocked artery, treated with a stent.",
               "Coronary artery disease, single vessel", "Coronary angioplasty with drug-eluting stent",
               [("ICU Charges (2 days @ 14,000)", 28000), ("Room Rent - Single Private (3 days @ 8,000)", 24000),
                ("Cardiologist and Procedure Fees", 95000), ("Cath Lab Charges", 60000),
                ("Drug-eluting Stent", 75000), ("Pharmacy - Medicines and Drugs", 22000),
                ("Laboratory Tests and Echocardiography", 14000)], 5,
               "PARTIAL_APPROVAL", "Cardiac admission above the adjuster's approval limit, escalated to a supervisor", 4,
               [_act("ESCALATE", 1, notes="Payable is above my approval limit; cardiac case for supervisor sign-off.")]))
    B.append(H("CLM-H-1104", "CS-HLT-24-000648", "2025-08-03", "Riverside Community Hospital",
               "Fever with chills every other day; admitted with falciparum malaria.",
               "Plasmodium falciparum malaria", "Medical management with antimalarials",
               [("Room Rent - General Ward (3 days @ 3,200)", 9600), ("Consultant Physician Fees", 7000),
                ("Pharmacy - Antimalarials", 6400), ("Laboratory Tests - Smear and Platelets", 3800)], 3,
               "PARTIAL_APPROVAL", "Room rent within the cap: only the deductible and co-pay apply", 52,
               [_act("APPROVE", 4)]))
    B.append(H("CLM-H-1105", "CS-HLT-23-000655", "2025-12-02", "Lakeview Multispeciality Hospital",
               "Severe breathlessness not settling with inhalers; admitted to the ICU.",
               "Acute exacerbation of bronchial asthma", "Medical management, nebulisation and steroids",
               [("ICU Charges (2 days @ 12,500)", 25000), (f"{room} (2 days @ 5,000)", 10000),
                ("Pulmonologist Fees", 12000), ("Pharmacy - Nebulisation and Steroids", 9600),
                ("Laboratory Tests and Chest X-Ray", 5400)], 4,
               "PARTIAL_APPROVAL", "ICU charges above the ICU daily cap", 12))
    B.append(H("CLM-H-1106", "CS-HLT-22-000662", "2025-09-22", "Greenfield General Hospital",
               "Swelling in the right groin for some months; planned surgical repair.",
               "Right inguinal hernia", "Laparoscopic hernia repair with mesh",
               [(f"{room} (2 days @ 5,000)", 10000), ("Surgeon Fees", 38000), ("Operation Theatre Charges", 15000),
                ("Mesh and Medicines", 14000), ("Laboratory Tests", 3500)], 2,
               "PARTIAL_APPROVAL", "Hernia after the 24-month specified-disease waiting period, so it is covered", 27,
               [_act("APPROVE", 5, notes="Mesh charge billed twice on the hospital ledger; approved INR 2,000 less.",
                     payable_delta=-2000)]))
    B.append(H("CLM-H-1107", "CS-HLT-25-000679", "2025-09-28", "Sunrise Care Hospital",
               "Injured in a road traffic accident while commuting; fracture of the left leg.",
               "Fracture shaft of left tibia following road traffic accident", "Intramedullary nailing of tibia",
               [(f"{room} (3 days @ 5,000)", 15000), ("Orthopaedic Surgeon Fees", 40000),
                ("Operation Theatre Charges", 14000), ("Implants - Tibial Nail", 30000), ("X-Ray and Diagnostics", 4000)],
               3, "PARTIAL_APPROVAL",
               "Accident 18 days after cover began: exempt from the 30-day initial waiting period", 33))
    B.append(H("CLM-H-1108", "CS-HLT-24-000686", "2025-01-18", "Riverside Community Hospital",
               "Cough, fever and chest pain; admitted with pneumonia of the right lower lobe.",
               "Right lower lobe pneumonia", "Medical management with IV antibiotics",
               [(f"{room} (4 days @ 4,500)", 18000), ("Consultant Physician Fees", 10000),
                ("Pharmacy - Medicines and Drugs", 15500), ("Laboratory Tests and Chest X-Ray", 6800)], 4,
               "PARTIAL_APPROVAL", "Incident in January 2025, so the 2024.1 wording applies (higher deductible and co-pay)",
               58, [_act("APPROVE", 12)]))
    B.append(H("CLM-H-1109", "CS-HLT-23-000693", "2026-02-11", "Lakeview Multispeciality Hospital",
               "Sudden pain in the lower right abdomen with vomiting; operated the same night.",
               "Acute appendicitis", "Laparoscopic appendicectomy",
               [(f"{room} (2 days @ 6,000)", 12000), ("Surgeon Fees", 40000), ("Operation Theatre Charges", 15000),
                ("Pharmacy - Medicines and Drugs", 8000), ("Laboratory Tests and CT Abdomen", 7000),
                ("Consumables - Gloves, Masks, Admission Kit", 2500)], 2,
               "PARTIAL_APPROVAL", "Emergency surgery; room-rent cap and consumables exclusion apply", 2))
    B.append(H("CLM-H-1110", "CS-HLT-24-000707", "2025-12-21", "Greenfield General Hospital",
               "Twisted the right knee during a football match; ligament injury confirmed on MRI.",
               "Anterior cruciate ligament tear, right knee (sports injury)", "Arthroscopic ligament reconstruction",
               [(f"{room} (2 days @ 5,000)", 10000), ("Orthopaedic Surgeon Fees", 55000),
                ("Operation Theatre Charges", 18000), ("Implants - Graft Fixation", 26000), ("MRI and Diagnostics", 9000)],
               2, "PARTIAL_APPROVAL", "Sports injury; covered, paid after the deductible and co-pay", 19,
               [_act("APPROVE", 3)]))
    B.append(H("CLM-H-1111", "CS-HLT-22-000714", "2025-10-30", "Sunrise Care Hospital",
               "Scheduled day-care chemotherapy cycle for breast carcinoma.",
               "Carcinoma of the left breast", "Day-care chemotherapy, cycle 3",
               [("Room Rent - Day Care (1 day @ 3,000)", 3000), ("Oncologist Fees", 8000),
                ("Pharmacy - Chemotherapy Drugs", 64000), ("Laboratory Tests", 4500)], 0,
               "PARTIAL_APPROVAL", "Day-care cancer treatment; deductible and co-pay apply", 7))
    B.append(H("CLM-H-1112", "CS-HLT-25-000721", "2025-09-12", "Riverside Community Hospital",
               "High fever with bleeding gums; admitted to the ICU with severe dengue.",
               "Dengue haemorrhagic fever", "Medical management with platelet transfusion",
               [("ICU Charges (3 days @ 11,000)", 33000), (f"{room} (4 days @ 5,000)", 20000),
                ("Consultant and Intensivist Fees", 36000), ("Pharmacy - Medicines and Drugs", 38000),
                ("Platelet Transfusion and Laboratory Tests", 35000)], 7,
               "PARTIAL_APPROVAL", "Medium risk: an early claim at 54% of the sum insured, still payable after caps", 15,
               [_act("APPROVE", 2, notes="Platelet counts on the lab reports support the ICU stay.")]))
    # ---- health: not covered under a clause
    B.append(H("CLM-H-1121", "CS-HLT-24-000738", "2025-12-09", "Clearsight Eye Institute",
               "Gradual blurring of vision in the right eye; planned surgery.",
               "Senile cataract, right eye", "Cataract surgery with IOL implant",
               [("Room Rent - Day Care (1 day @ 3,000)", 3000), ("Surgeon Fees - Phacoemulsification", 30000),
                ("Intraocular Lens and Medicines", 22000), ("Diagnostic Tests - Biometry", 2500)], 0,
               "RECOMMEND_REJECT", "Cataract 13 months into cover, inside the 24-month waiting period (clause 3.3)", 36,
               [_act("REJECT", 3, notes="Cataract is a specified condition; 24-month waiting period not yet served (clause 3.3).")]))
    B.append(H("CLM-H-1122", "CS-HLT-25-000745", "2025-10-16", "Riverside Urology Centre",
               "Severe flank pain; diagnosed with a kidney stone and treated with ureteroscopic lithotripsy.",
               "Left renal calculus (kidney stone), 8 mm", "Ureteroscopic lithotripsy (URSL)",
               [(f"{room} (2 days @ 4,800)", 9600), ("Urologist Fees", 36000), ("Operation Theatre Charges", 15000),
                ("Pharmacy - Medicines and Drugs", 7000), ("Diagnostic Tests - CT KUB", 6200)], 2,
               "RECOMMEND_REJECT", "Kidney stone eight months into cover, inside the 24-month waiting period", 22,
               [_act("REJECT", 4, notes="Kidney stone within the specified-disease waiting period (clause 3.3).")]))
    B.append(H("CLM-H-1123", "CS-HLT-25-000752", "2025-10-17", "Greenfield General Hospital",
               "High fever with body ache and vomiting; admitted for viral fever.",
               "Viral fever with dehydration", "Medical management with IV fluids",
               [(f"{room} (3 days @ 4,500)", 13500), ("Consultant Physician Fees", 7500),
                ("Pharmacy - Medicines and Drugs", 6200), ("Laboratory Tests", 4800)], 3,
               "RECOMMEND_REJECT", "Illness 16 days after cover began, inside the 30-day initial waiting period", 11,
               [_act("REJECT", 2, notes="Illness within the 30-day initial waiting period (clause 3.1).")]))
    B.append(H("CLM-H-1124", "CS-HLT-23-000769", "2025-11-04", "Silverline Day Surgery Centre",
               "Elective liposuction of the abdomen and flanks for weight reduction.",
               "Localised adiposity", "Liposuction (cosmetic)",
               [("Room Rent - Single Private (1 day @ 6,000)", 6000), ("Surgeon Fees", 85000),
                ("Operation Theatre Charges", 20000), ("Pharmacy - Medicines and Drugs", 6000)], 1,
               "RECOMMEND_REJECT", "Cosmetic procedure, excluded under clause 4.1", 47,
               [_act("REJECT", 6, notes="Cosmetic procedure; excluded under clause 4.1.")]))
    B.append(H("CLM-H-1125", "CS-HLT-24-000776", "2025-08-25", "Motherhood Care Hospital",
               "Admitted at full term; baby born by caesarean section.",
               "Full-term pregnancy", "Lower segment caesarean section",
               [(f"{room} (4 days @ 5,000)", 20000), ("Obstetrician Fees", 45000), ("Operation Theatre Charges", 18000),
                ("Pharmacy - Medicines and Drugs", 9000), ("Laboratory Tests", 4000)], 4,
               "RECOMMEND_REJECT", "Maternity, excluded under clause 4.4", 5))
    B.append(H("CLM-H-1126", "CS-HLT-24-000783", "2025-11-12", "Lakeview Multispeciality Hospital",
               "Vomiting and loose stools for two days; admitted with dehydration.",
               "Acute gastroenteritis with dehydration", "Medical management with IV fluids",
               [(f"{room} (2 days @ 4,500)", 9000), ("Consultant Physician Fees", 6000),
                ("Pharmacy - Medicines and IV Fluids", 5800), ("Laboratory Tests", 3200)], 2,
               "RECOMMEND_REJECT", "Policy expired on 2025-09-30, before the admission", 29,
               [_act("REJECT", 3, notes="Policy had lapsed before the admission date.")]))
    B.append(H("CLM-H-1127", "CS-HLT-23-000790", "2025-12-28", "Sunrise Care Hospital",
               "Severe upper abdominal pain after a weekend of heavy alcohol intake.",
               "Acute pancreatitis related to alcohol intake", "Medical management",
               [(f"{room} (5 days @ 5,000)", 25000), ("Gastroenterologist Fees", 14000),
                ("Pharmacy - Medicines and Drugs", 21000), ("Laboratory Tests and CT Abdomen", 12000)], 5,
               "RECOMMEND_REJECT", "Alcohol-related condition, excluded under clause 4.2", 1))
    # ---- health: documents missing
    B.append(H("CLM-H-1131", "CS-HLT-24-000805", "2025-11-26", "Riverside Community Hospital",
               "Fever with severe joint pains; admitted for chikungunya.", "Chikungunya fever", "Medical management",
               [(f"{room} (3 days @ 4,500)", 13500), ("Consultant Physician Fees", 7000),
                ("Pharmacy - Medicines and Drugs", 5600), ("Laboratory Tests - Serology", 4400)], 3,
               "REQUEST_INFO", "Discharge summary not submitted", 18,
               [_act("REQUEST_INFO", 2, notes="Asked the hospital for the discharge summary.")], skip_discharge=True))
    B.append(H("CLM-H-1132", "CS-HLT-23-000812", "2025-12-14", "Greenfield General Hospital",
               "Burning urination and high fever; admitted with a urinary tract infection.",
               "Acute pyelonephritis", "Medical management with IV antibiotics", [], 3,
               "REQUEST_INFO", "Hospital bill not submitted, so the amount cannot be assessed", 6,
               skip_bill=True, form_amount=28400))
    B.append(H("CLM-H-1133", "CS-HLT-24-000829", "2026-03-03", "Lakeview Multispeciality Hospital",
               "Persistent cough with fever; admitted for acute bronchitis.", "Acute bronchitis", "Medical management",
               [(f"{room} (2 days @ 4,500)", 9000), ("Consultant Physician Fees", 5000),
                ("Pharmacy - Medicines and Drugs", 4600), ("Laboratory Tests and Chest X-Ray", 3400)], 2,
               "REQUEST_INFO", "Discharge summary not submitted", 3, skip_discharge=True))
    # ---- health: refer for investigation
    B.append(H("CLM-H-1141", "CS-HLT-25-000836", "2025-10-05", "Sunrise Care Hospital",
               "High fever with low blood pressure; admitted to the ICU with a severe kidney infection.",
               "Acute pyelonephritis with sepsis", "Medical management in ICU, haemodialysis",
               [("ICU Charges (6 days @ 16,000)", 96000), ("Room Rent - Single Private (4 days @ 7,000)", 28000),
                ("Intensivist and Nephrologist Fees", 52000), ("Pharmacy - IV Antibiotics", 58000),
                ("Dialysis and Laboratory Tests", 30000)], 10,
               "INVESTIGATE", "High risk: 88% of the sum insured, 65 days after cover began", 24,
               [_act("INVESTIGATE", 5, notes="Referred to investigation: 88% of sum insured 65 days into cover.")]))
    B.append(H("CLM-H-1142", "CS-HLT-25-000843", "2025-09-30", "Greenfield General Hospital",
               "Pain in the upper right abdomen with fever; gallbladder removed.",
               "Acute calculous cholecystitis", "Laparoscopic cholecystectomy",
               [(f"{room} (3 days @ 5,000)", 15000), ("Surgeon Fees", 45000), ("Operation Theatre Charges", 18000),
                ("Pharmacy - Medicines and Drugs", 16000), ("Laboratory Tests and Ultrasound", 14000)], 3,
               "INVESTIGATE", "High risk: claim form asks for 1,52,000 against a 1,08,000 bill, 77 days into cover", 14,
               form_amount=152000))
    B.append(H("CLM-H-1143", "CS-HLT-24-000611", "2025-10-14", "Lakeview Multispeciality Hospital",
               "Claim for hospitalisation for typhoid fever.", "Typhoid fever", "Medical management with IV antibiotics",
               [(f"{room} (4 days @ 5,500)", 22000), ("Consultant Physician Fees", 9500),
                ("Pharmacy - Medicines and Drugs", 11800), ("Laboratory Tests - Widal and Blood Culture", 4200),
                ("Consumables - Gloves, Masks, Admission Kit", 1600)], 4,
               "INVESTIGATE", "Possible duplicate of CLM-H-1101 (same policy, date and amount)", 8,
               [_act("REJECT", 1, notes="Duplicate of CLM-H-1101, which is already settled.")]))

    # ---- motor: covered, paid after depreciation and the deductible
    B.append(M("CLM-M-2101", "CS-MTR-25-001411", "2025-07-12", "Compact SUV 1199cc", 1199, "2025-03-18", "MH-12-SY-3307",
               "Side-swiped by a two-wheeler while parked; left front door and fender dented.",
               [("Left Front Door Panel (metal) - replace", 24000), ("Front Fender (metal) - repair", 8000),
                ("Painting Material", 7000), ("Denting and Fitting Labour", 6500)],
               "PARTIAL_APPROVAL", "Nearly new car: no metal depreciation, paint at 50% and the deductible", 44,
               [_act("APPROVE", 5)]))
    B.append(M("CLM-M-2102", "CS-MTR-25-001428", "2025-08-30", "SUV 1997cc", 1997, "2023-01-15", "KA-51-SY-7714",
               "Hit a stray animal on the highway at night; front bumper, bonnet and headlamp damaged.",
               [("Front Bumper (plastic) - replace", 18000), ("Bonnet (metal) - replace", 42000),
                ("Headlamp Assembly (plastic)", 16000), ("Radiator Grille (plastic)", 6500),
                ("Painting Material", 9000), ("Denting and Fitting Labour", 12000)],
               "PARTIAL_APPROVAL", "Engine above 1500cc: higher deductible; metal at 15% for a 31-month-old car", 31,
               [_act("APPROVE", 8, notes="Surveyor photos match the estimate.")]))
    B.append(M("CLM-M-2103", "CS-MTR-25-001435", "2025-10-21", "Hatchback 1197cc", 1197, "2022-08-10", "KA-03-SY-5521",
               "A branch came down on the car during a storm and shattered the front windshield.",
               [("Front Windshield Glass - replace", 18500), ("Windshield Fitting Labour", 2500)],
               "PARTIAL_APPROVAL", "Glass carries no depreciation: only the deductible applies", 13,
               [_act("APPROVE", 1)]))
    B.append(M("CLM-M-2104", "CS-MTR-25-001442", "2025-11-08", "Sedan 1497cc", 1497, "2019-02-11", "TN-09-SY-2048",
               "Reversed into a pillar in a basement car park; rear bumper and boot lid damaged.",
               [("Rear Bumper (plastic) - replace", 9000), ("Boot Lid Panel (metal) - repair", 14000),
                ("Tail Lamp Assembly (plastic)", 4200), ("Painting Material", 5000), ("Denting and Fitting Labour", 6000)],
               "PARTIAL_APPROVAL", "Older car: 40% depreciation on metal parts", 39,
               [_act("APPROVE", 34, notes="Approved after a second survey; settlement period missed.")]))
    B.append(M("CLM-M-2105", "CS-MTR-25-001459", "2025-12-03", "Scooter 125cc", 125, "2023-06-01", "KA-01-SY-8890",
               "Skidded on a wet road; front panel, mirror and headlamp broken.",
               [("Front Panel (plastic) - replace", 3800), ("Rear View Mirror Glass", 900),
                ("Headlamp Assembly (plastic)", 2600), ("Fitting Labour", 1200)],
               "PARTIAL_APPROVAL", "Two-wheeler: plastic parts at 50% and the deductible", 3))
    B.append(M("CLM-M-2106", "CS-MTR-25-001466", "2026-01-17", "SUV 2179cc", 2179, "2024-09-05", "MH-14-SY-6602",
               "Multi-vehicle collision on the expressway; front and right side extensively damaged.",
               [("Front Bumper (plastic) - replace", 22000), ("Bonnet (metal) - replace", 48000),
                ("Right Front Door Panel (metal) - replace", 38000), ("Right Rear Door Panel (metal) - replace", 36000),
                ("Headlamp Assembly (plastic)", 28000), ("Front Windshield Glass", 26000),
                ("Radiator Support Panel (metal)", 18000), ("Painting Material", 24000),
                ("Denting and Fitting Labour", 40000)],
               "PARTIAL_APPROVAL", "Large repair above the adjuster's limit: escalated, then approved by a supervisor", 26,
               [_act("ESCALATE", 2, notes="Above my approval limit; needs supervisor sign-off."),
                _act("APPROVE", 4, role="supervisor", notes="Reviewed the survey report; approved.")]))
    B.append(M("CLM-M-2107", "CS-MTR-25-001473", "2025-12-29", "Hatchback 1199cc", 1199, "2024-12-20", "KA-05-SY-1736",
               "Rear-ended in slow traffic; rear bumper and tail lamps damaged.",
               [("Rear Bumper (plastic) - replace", 11000), ("Tail Lamp Assembly (plastic) x2", 9800),
                ("Boot Lid Panel (metal) - repair", 7000), ("Painting Material", 5200), ("Denting and Fitting Labour", 4500)],
               "PARTIAL_APPROVAL", "One-year-old car: metal at 5%", 10))
    B.append(M("CLM-M-2108", "CS-MTR-25-001480", "2026-02-14", "Sedan 1462cc", 1462, "2021-11-02", "TS-08-SY-4419",
               "Front wheel dropped into an open drain; front bumper and fender damaged.",
               [("Front Bumper (plastic) - replace", 12500), ("Front Fender (metal) - replace", 15000),
                ("Painting Material", 5500), ("Denting and Fitting Labour", 5000)],
               "PARTIAL_APPROVAL", "Car over four years old: metal at 35%", 6))
    # ---- motor: not covered under a clause
    B.append(M("CLM-M-2111", "CS-MTR-25-001497", "2025-11-30", "Sedan 1498cc", 1498, "2022-05-05", "DL-08-SY-9031",
               "Lost control late at night and struck a parked truck.",
               [("Front Bumper (plastic) - replace", 16000), ("Bonnet (metal) - replace", 34000),
                ("Headlamp Assembly (plastic)", 12000), ("Denting and Fitting Labour", 10000)],
               "RECOMMEND_REJECT", "Driving under the influence, excluded under clause 3.1", 34,
               [_act("REJECT", 4, notes="Police report records a positive breath analyser test (clause 3.1).")],
               police="Driver examined at the spot. Breath analyser test positive; driver was under the influence of alcohol."))
    B.append(M("CLM-M-2112", "CS-MTR-25-001503", "2025-12-11", "Hatchback 1197cc", 1197, "2020-09-09", "KA-02-SY-6258",
               "Swerved to avoid a pedestrian and hit a road divider.",
               [("Front Bumper (plastic) - replace", 9500), ("Front Fender (metal) - repair", 7000),
                ("Painting Material", 4000), ("Denting and Fitting Labour", 3500)],
               "RECOMMEND_REJECT", "Driving licence expired before the accident (clause 3.2)", 17,
               [_act("REJECT", 3, notes="Licence expired on 2025-08-31 and was not renewed (clause 3.2).")],
               police="Driver's licence expired on 2025-08-31 and had not been renewed.", licence_valid_till="2025-08-31"))
    B.append(M("CLM-M-2113", "CS-MTR-25-001510", "2025-09-07", "Sedan 1497cc", 1497, "2020-01-20", "MH-02-SY-1184",
               "Engine seized on the highway; the workshop reports a mechanical breakdown from oil starvation.",
               [("Engine Block (metal) - overhaul", 68000), ("Engine Labour", 12000)],
               "RECOMMEND_REJECT", "Mechanical breakdown, excluded under clause 3.3", 28,
               [_act("REJECT", 2, notes="Mechanical breakdown is excluded (clause 3.3).")],
               police="No collision. Vehicle towed from the highway after the engine failed."))
    B.append(M("CLM-M-2114", "CS-MTR-25-001527", "2025-10-24", "SUV 1956cc", 1956, "2023-03-03", "UK-07-SY-3390",
               "Hit by falling rocks and slid into a barrier on a mountain road during a trip in Nepal.",
               [("Bonnet (metal) - replace", 46000), ("Front Windshield Glass", 24000),
                ("Front Bumper (plastic) - replace", 19000), ("Denting and Fitting Labour", 15000)],
               "RECOMMEND_REJECT", "Loss outside India, excluded under clause 3.4", 9,
               police="Report filed with the local police in Nepal."))
    B.append(M("CLM-M-2115", "CS-MTR-25-001534", "2025-08-20", "Hatchback 1197cc", 1197, "2021-04-14", "GJ-01-SY-7012",
               "Scraped against a bus at a junction; right side doors damaged.",
               [("Right Front Door Panel (metal) - repair", 12000), ("Right Rear Door Panel (metal) - repair", 11000),
                ("Painting Material", 6000), ("Denting and Fitting Labour", 5000)],
               "RECOMMEND_REJECT", "Accident 12 days before the policy began", 21,
               [_act("REJECT", 2, notes="Loss occurred before the policy start date.")]))
    # ---- motor: documents missing
    B.append(M("CLM-M-2121", "CS-MTR-25-001541", "2025-12-19", "Hatchback 1199cc", 1199, "2022-02-22", "KA-41-SY-2675",
               "Rear-ended at a toll plaza; rear bumper damaged.",
               [("Rear Bumper (plastic) - replace", 10500), ("Painting Material", 3500), ("Fitting Labour", 2000)],
               "REQUEST_INFO", "Driving licence not submitted", 16,
               [_act("REQUEST_INFO", 1, notes="Requested a copy of the driving licence.")], skip_licence=True))
    B.append(M("CLM-M-2122", "CS-MTR-25-001558", "2026-01-26", "Sedan 1497cc", 1497, "2023-09-30", "KA-53-SY-4480",
               "Side mirror and door damaged by a passing truck.", [],
               "REQUEST_INFO", "Repair estimate not submitted, so the amount cannot be assessed", 4,
               skip_estimate=True, form_amount=26000))
    # ---- motor: refer for investigation
    B.append(M("CLM-M-2131", "CS-MTR-25-001565", "2025-12-06", "Hatchback 1197cc", 1197, "2021-07-07", "KA-19-SY-0559",
               "Car rolled over on a ghat road; extensive body damage.",
               [("Roof Panel (metal) - replace", 70000), ("Left Door Panels (metal) - replace", 80000),
                ("Bonnet (metal) - replace", 40000), ("Front Bumper (plastic) - replace", 18000),
                ("Front Windshield Glass", 22000), ("Headlamp Assembly (plastic)", 14000),
                ("Painting Material", 32000), ("Denting and Fitting Labour", 60000)],
               "INVESTIGATE", "High risk: 84% of the insured value, 35 days after cover began", 20,
               [_act("INVESTIGATE", 3, notes="Referred to investigation: near total loss five weeks into cover.")]))
    B.append(M("CLM-M-2132", "CS-MTR-25-001572", "2025-10-25", "Sedan 1497cc", 1497, "2019-10-10", "WB-02-SY-3815",
               "Hit from the side at an intersection; left doors and pillar damaged.",
               [("Left Front Door Panel (metal) - replace", 36000), ("Left Rear Door Panel (metal) - replace", 34000),
                ("Centre Pillar Panel (metal) - repair", 22000), ("Painting Material", 12000),
                ("Denting and Fitting Labour", 16000)],
               "INVESTIGATE", "High risk: claim form asks for 1,65,000 against a 1,20,000 estimate, 66 days into cover", 37,
               form_amount=165000))
    return B


def write_demo_book() -> list[dict]:
    root = CLM / "demo_book"
    out = []
    for c in demo_book():
        d = root / c["claim_number"]
        d.mkdir(parents=True, exist_ok=True)
        c.setdefault("form_amount", sum(a for _, a in c["items"]))
        files = {"claim_form.txt": claim_form(c)}
        if c["claim_type"] == "health":
            if not c.get("skip_bill"):
                files["hospital_bill.txt"] = bill("FINAL HOSPITAL BILL", c, c["items"],
                                                  {"Hospital": c["hospital"], "Bill Number": f"HB-{c['claim_number'][-4:]}",
                                                   "Admission Date": c["admit"], "Discharge Date": c["disch"]})
            if not c.get("skip_discharge"):
                files["discharge_summary.txt"] = discharge(c, c["admit"], c["disch"], c["diagnosis"], c["procedure"],
                                                           c["notes"])
        else:
            if not c.get("skip_estimate"):
                files["repair_estimate.txt"] = bill("WORKSHOP REPAIR ESTIMATE", c, c["items"],
                                                    {"Workshop": "Highway Motors Service Centre (fictional)",
                                                     "Estimate Number": f"RE-{c['claim_number'][-4:]}",
                                                     "Vehicle Registration": c["form_extra"]["Vehicle Registration"]})
            if not c.get("skip_licence"):
                files["driving_licence.txt"] = licence(c)
            files["police_report.txt"] = police_report(c, c["police"])
        for name, body in files.items():
            (d / name).write_text(body, encoding="utf-8")
        out.append({"claim_number": c["claim_number"], "claim_type": c["claim_type"], "policy_number": c["policy_number"],
                    "claimant_name": c["claimant"], "incident_date": c["incident_date"], "description": c["narrative"],
                    "documents": sorted(files), "expected_recommendation": c["expected"], "scenario": c["story"],
                    "age_days": c["age_days"], "history": c["history"]})
    return out


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
    return E


def write_evaluation_packets() -> None:
    for c in evaluation_claims():
        d = EVAL / c["claim_number"]
        d.mkdir(parents=True, exist_ok=True)
        c["form_amount"] = sum(a for _, a in c["items"])
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


def portfolio(n: int = 1000, fraud_rate: float = 0.08) -> None:
    """Synthetic claim portfolio with labelled, injected anomaly patterns.

    The injection rate is a demo parameter, not an estimate of real-world fraud prevalence.
    """
    rng = random.Random(2025)
    rows = []
    for i in range(1, n + 1):
        line = rng.choices(["health", "motor"], [0.65, 0.35])[0]
        si = rng.choice([300000, 500000, 1000000]) if line == "health" else rng.choice([350000, 500000, 800000])
        start = date(2024, 4, 1) + timedelta(days=rng.randint(0, 420))
        incident = start + timedelta(days=rng.randint(45, 330))
        amount = round(min(si * 0.9, rng.lognormvariate(10.6 if line == "health" else 10.2, 0.6)), -2)
        prior = rng.choices([0, 1, 2], [0.8, 0.15, 0.05])[0]
        bill_total, dup = amount, 0
        injected: list[str] = []
        if rng.random() < fraud_rate:
            injected = rng.sample(PATTERNS, rng.choice([1, 1, 2]))
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
    (POL / "insured_policies.json").write_text(json.dumps([
        dict(policy_number=a, product_code=b, holder_name=c, start_date=d, end_date=e, sum_insured=f)
        for a, b, c, d, e, f in INSURED + DEMO_INSURED], indent=2), encoding="utf-8")
    scen = write_claim_packets()
    book = write_demo_book()
    (CLM / "demo_book.json").write_text(json.dumps(book, indent=2), encoding="utf-8")
    write_demo_upload()
    write_evaluation_packets()
    write_ingest_demo()
    (CLM / "scenarios.json").write_text(json.dumps(scen, indent=2), encoding="utf-8")
    portfolio()
    print(f"policies: {len(list(POL.glob('*.md')))}, claims: {len(scen)} golden + {len(book)} demo book, portfolio rows: 1000")


if __name__ == "__main__":
    main()
