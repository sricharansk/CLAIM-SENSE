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
                      "Valid Till: 2036-03-31", "Class: LMV"]) + "\n"


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
        for a, b, c, d, e, f in INSURED], indent=2), encoding="utf-8")
    scen = write_claim_packets()
    write_demo_upload()
    (CLM / "scenarios.json").write_text(json.dumps(scen, indent=2), encoding="utf-8")
    portfolio()
    print(f"policies: {len(list(POL.glob('*.md')))}, claims: {len(scen)}, portfolio rows: 1000")


if __name__ == "__main__":
    main()
