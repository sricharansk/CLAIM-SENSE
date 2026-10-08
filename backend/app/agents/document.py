"""Document Intelligence Agent: text extraction, document classification and fact extraction.

Extraction is deterministic (labelled fields + itemised charge lines), so every fact carries the
exact source line it came from. Uploaded text is treated as data and never executed or obeyed.
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass

from pypdf import PdfReader

DOC_TYPES = [
    ("claim_form", ["claim form"]),
    ("discharge_summary", ["discharge summary"]),
    ("hospital_bill", ["hospital bill", "final bill", "inpatient bill"]),
    ("repair_estimate", ["repair estimate", "workshop estimate"]),
    ("driving_licence", ["driving licence", "driving license"]),
    ("police_report", ["police", "fir number", "accident report"]),
]

FIELD_MAP = {
    "policy number": "policy_number", "claimant name": "claimant_name", "patient name": "patient_name",
    "patient/insured name": "patient_name", "name": "licence_holder", "incident date": "incident_date",
    "date of accident": "incident_date", "admission date": "admission_date", "discharge date": "discharge_date",
    "diagnosis": "diagnosis", "procedure": "procedure", "claimed amount": "claimed_amount", "hospital": "hospital",
    "claim type": "claim_type", "vehicle registration": "vehicle_registration",
    "vehicle make and model": "vehicle_model", "date of first registration": "vehicle_first_registration",
    "engine capacity cc": "engine_cc", "fir number": "fir_number", "licence number": "licence_number",
    "valid till": "licence_valid_till", "workshop": "workshop", "bill number": "bill_number",
    "estimate number": "estimate_number",
}
NARRATIVE_HEADERS = {"description of loss:": "narrative", "clinical notes:": "clinical_notes", "findings:": "police_findings"}
FIELD_RE = re.compile(r"^\s*([A-Za-z/ ]{3,40}?)\s*:\s*(.+?)\s*$")
ITEM_RE = re.compile(r"^\s*(.+?)\s{2,}((?:\d{1,3}(?:,\d{2,3})+|\d+)\.\d{2})\s*$")

CATEGORY_RULES = [
    ("consumables", ["consumable", "gloves", "mask", "admission kit", "toiletr"]),
    ("non_medical", ["registration charge", "file charge", "attendant", "food"]),
    ("icu", ["icu", "intensive care"]),
    ("room_rent", ["room rent", "room charges", "ward"]),
    ("professional_fees", ["surgeon", "consultant", "doctor", "anaesthetist", "intensivist", "physician"]),
    ("ot_charges", ["operation theatre", "ot charges"]),
    ("medicines", ["pharmacy", "medicine", "drug", "implant", "lens"]),
    ("diagnostics", ["laboratory", "diagnostic", "x-ray", "ct ", "mri", "scan", "test", "biometry"]),
    ("equipment", ["ventilator", "equipment", "oxygen"]),
    ("glass", ["glass", "windshield", "windscreen"]),
    ("paint", ["paint"]),
    ("labour", ["labour", "labor", "fitting", "denting"]),
    ("parts_plastic", ["plastic", "rubber", "nylon", "bumper", "lamp"]),
    ("parts_fibre", ["fibre", "fiber"]),
    ("parts_metal", ["metal", "panel", "bonnet", "door", "fender", "boot lid"]),
]


@dataclass
class Fact:
    name: str
    value: str
    confidence: float
    line: int | None
    source: str


def extract_text(filename: str, data: bytes) -> tuple[str, int]:
    if filename.lower().endswith(".pdf") or data[:5] == b"%PDF-":
        reader = PdfReader(io.BytesIO(data))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages), len(pages)
    return data.decode("utf-8", errors="replace"), 1


def classify(text: str, filename: str = "") -> str:
    head = (text[:400] + " " + filename.replace("_", " ")).lower()
    for doc_type, keys in DOC_TYPES:
        if any(k in head for k in keys):
            return doc_type
    return "other"


def categorize(description: str) -> tuple[str, float]:
    d = description.lower() + " "
    for cat, keys in CATEGORY_RULES:
        if any(k in d for k in keys):
            return cat, 0.9
    return "other", 0.6


def parse_amount(s: str) -> float:
    return float(s.replace(",", "").replace("INR", "").strip())


def extract_facts(text: str) -> list[Fact]:
    facts: list[Fact] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        low = raw.strip().lower()
        if low in NARRATIVE_HEADERS:
            j, buf = i + 1, []
            while j < len(lines) and lines[j].strip():
                buf.append(lines[j].strip())
                j += 1
            if buf:
                facts.append(Fact(NARRATIVE_HEADERS[low], " ".join(buf), 0.95, i + 2, " ".join(buf)[:300]))
            i = j
            continue
        if m := ITEM_RE.match(raw):
            desc, amt = m.group(1).strip(), parse_amount(m.group(2))
            if desc.lower().startswith("total"):
                facts.append(Fact("document_total", f"{amt:.2f}", 0.98, i + 1, raw.strip()))
            else:
                cat, conf = categorize(desc)
                facts.append(Fact("line_item", json.dumps({"description": desc, "amount": amt, "category": cat}),
                                  conf, i + 1, raw.strip()))
        elif m := FIELD_RE.match(raw):
            label = m.group(1).strip().lower()
            if label in FIELD_MAP:
                value = m.group(2).strip()
                if FIELD_MAP[label] == "claimed_amount":
                    value = f"{parse_amount(value):.2f}"
                facts.append(Fact(FIELD_MAP[label], value, 0.98, i + 1, raw.strip()))
        i += 1
    return facts
