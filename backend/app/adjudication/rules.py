"""Deterministic adjudication tool. All money is Decimal; the LLM never touches these numbers.

Each rule appends a step to a transparent waterfall that cites the policy clause it applies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..config import settings

ZERO = Decimal("0.00")
DAYS_AT_RATE = re.compile(r"(\d+)\s*days?\s*@\s*([\d,]+)", re.I)


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class LineItem:
    description: str
    amount: Decimal
    category: str


@dataclass
class Step:
    rule_id: str
    label: str
    adjustment: Decimal
    running_total: Decimal
    clause_ref: str | None = None
    detail: str = ""

    def as_dict(self) -> dict:
        return {"rule_id": self.rule_id, "label": self.label, "adjustment": str(self.adjustment),
                "running_total": str(self.running_total), "clause_ref": self.clause_ref, "detail": self.detail}


@dataclass
class Adjudication:
    claimed_amount: Decimal
    gross_billed: Decimal
    non_covered: Decimal = ZERO
    deductible: Decimal = ZERO
    copay: Decimal = ZERO
    depreciation: Decimal = ZERO
    payable: Decimal = ZERO
    steps: list[Step] = field(default_factory=list)
    rules_version: str = settings.rules_version

    def as_dict(self) -> dict:
        return {"claimed_amount": str(self.claimed_amount), "gross_billed": str(self.gross_billed),
                "non_covered": str(self.non_covered), "deductible": str(self.deductible), "copay": str(self.copay),
                "depreciation": str(self.depreciation), "payable_amount": str(self.payable),
                "rules_version": self.rules_version, "waterfall": [s.as_dict() for s in self.steps]}


class _Waterfall:
    def __init__(self, start: Decimal, result: Adjudication):
        self.total, self.r = start, result

    def apply(self, rule_id: str, label: str, adjustment: Decimal, clause: str | None = None, detail: str = ""):
        adjustment = money(adjustment)
        self.total = money(self.total + adjustment)
        self.r.steps.append(Step(rule_id, label, adjustment, self.total, clause, detail))


def _start(items: list[LineItem], claimed: Decimal) -> tuple[Adjudication, _Waterfall]:
    gross = money(sum((i.amount for i in items), ZERO))
    r = Adjudication(claimed_amount=money(claimed), gross_billed=gross)
    w = _Waterfall(gross, r)
    r.steps.append(Step("R00_GROSS", "Itemised charges in submitted documents", gross, gross, None,
                        f"{len(items)} line items"))
    return r, w


def not_admissible(items: list[LineItem], claimed: Decimal, clause: str | None, reason: str) -> Adjudication:
    r, w = _start(items, claimed)
    w.apply("R99_NOT_ADMISSIBLE", "Claim not admissible under policy", -w.total, clause, reason)
    r.non_covered = r.gross_billed
    r.payable = ZERO
    return r


def adjudicate_health(items: list[LineItem], claimed: Decimal, terms: dict, sum_insured_available: Decimal) -> Adjudication:
    r, w = _start(items, claimed)
    non_payable = terms.get("non_payable_categories", {})
    limits = terms.get("limits", {})
    for it in items:
        if it.category in non_payable:
            w.apply("R10_NON_PAYABLE", f"Non-payable item: {it.description}", -it.amount, non_payable[it.category],
                    f"category '{it.category}' is not payable")
            r.non_covered += it.amount
            continue
        limit_key = terms.get("category_limits", {}).get(it.category)
        if limit_key and limit_key in limits:
            per_day = money(limits[limit_key]["amount"])
            m = DAYS_AT_RATE.search(it.description)
            if m:
                days, rate = int(m.group(1)), money(m.group(2).replace(",", ""))
                allowed = min(it.amount, per_day * days)
                if allowed < it.amount:
                    excess = it.amount - allowed
                    w.apply("R20_PER_DAY_LIMIT", f"{it.category.replace('_', ' ').title()} above per-day limit",
                            -excess, limits[limit_key]["clause"],
                            f"{days} days x min({rate}, {per_day}) = {money(allowed)} allowed of {it.amount}")
                    r.non_covered += excess
    admissible = w.total
    ded = min(money(terms["deductible"]["amount"]), max(admissible, ZERO))
    w.apply("R30_DEDUCTIBLE", "Deductible", -ded, terms["deductible"]["clause"], f"{ded} per claim")
    r.deductible = ded
    pct = Decimal(str(terms["copay_percent"]["value"]))
    copay = money(max(w.total, ZERO) * pct / Decimal(100))
    w.apply("R40_COPAY", f"Co-payment {pct}%", -copay, terms["copay_percent"]["clause"],
            f"{pct}% of {money(w.total + copay)}")
    r.copay = copay
    _cap(w, r, sum_insured_available, terms.get("max_liability_clause"), "Available sum insured")
    r.non_covered = money(r.non_covered)
    r.payable = max(w.total, ZERO)
    return r


def metal_depreciation(terms: dict, vehicle_age_months: int) -> int:
    for upto, pct in terms["depreciation"]["metal_by_age_months"]:
        if vehicle_age_months <= upto:
            return pct
    return terms["depreciation"]["metal_by_age_months"][-1][1]


def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


def adjudicate_motor(items: list[LineItem], claimed: Decimal, terms: dict, idv: Decimal,
                     vehicle_age_months: int, engine_cc: int | None) -> Adjudication:
    r, w = _start(items, claimed)
    dep = terms["depreciation"]
    flat = dep["flat_percent"]
    metal_pct = metal_depreciation(terms, vehicle_age_months)
    for it in items:
        pct = metal_pct if it.category == "parts_metal" else flat.get(it.category)
        if pct:
            cut = money(it.amount * Decimal(pct) / Decimal(100))
            label = f"Depreciation {pct}% on {it.description}"
            detail = (f"metal parts, vehicle age {vehicle_age_months} months" if it.category == "parts_metal"
                      else f"category '{it.category}'")
            w.apply("R15_DEPRECIATION", label, -cut, dep["clause"], detail)
            r.depreciation += cut
    d = terms["deductible"]
    amt = money(d["amount_above_1500cc"] if engine_cc and engine_cc > 1500 else d["amount"])
    ded = min(amt, max(w.total, ZERO))
    w.apply("R30_DEDUCTIBLE", "Compulsory deductible", -ded, d["clause"],
            f"engine {engine_cc or 'unknown'}cc")
    r.deductible = ded
    _cap(w, r, idv, terms.get("max_liability_clause"), "Insured declared value (IDV)")
    r.depreciation = money(r.depreciation)
    r.payable = max(w.total, ZERO)
    return r


def _covered(items: list[LineItem], terms: dict, w: _Waterfall, r: Adjudication) -> list[LineItem]:
    """Drop items whose category the product does not cover or lists as non-payable; return the rest."""
    cov = terms.get("covered_categories") or {}
    allowed = set(cov.get("categories", []))
    non_payable = terms.get("non_payable_categories", {})
    kept = []
    for it in items:
        if it.category in non_payable:
            w.apply("R10_NON_PAYABLE", f"Non-payable item: {it.description}", -it.amount, non_payable[it.category],
                    f"category '{it.category}' is not payable")
        elif allowed and it.category not in allowed:
            w.apply("R10_NOT_COVERED", f"Not a covered loss: {it.description}", -it.amount, cov.get("clause"),
                    f"category '{it.category}' is outside the cover")
        else:
            kept.append(it)
            continue
        r.non_covered += it.amount
    return kept


def adjudicate_indemnity(items: list[LineItem], claimed: Decimal, terms: dict, sum_insured_available: Decimal,
                         value_at_risk: Decimal | None = None, sum_insured: Decimal | None = None) -> Adjudication:
    """Reimbursement of assessed loss (travel and home): covered categories, depreciation, per-item and per-category
    limits, the average clause for under-insurance, a deductible and the sum-insured cap."""
    r, w = _start(items, claimed)
    kept = _covered(items, terms, w, r)
    dep = terms.get("depreciation") or {}
    item_caps = terms.get("item_caps", {})
    allowed: dict[str, Decimal] = {}
    for it in kept:
        value = it.amount
        pct = dep.get("flat_percent", {}).get(it.category)
        if pct:
            cut = money(value * Decimal(pct) / Decimal(100))
            w.apply("R15_DEPRECIATION", f"Depreciation {pct}% on {it.description}", -cut, dep["clause"],
                    f"category '{it.category}'")
            r.depreciation += cut
            value -= cut
        cap = item_caps.get(it.category)
        if cap and value > money(cap["amount"]):
            excess = value - money(cap["amount"])
            w.apply("R20_ITEM_LIMIT", f"{it.description} above the per-item limit", -excess, cap["clause"],
                    f"limit {money(cap['amount'])} per item")
            r.non_covered += excess
            value = money(cap["amount"])
        allowed[it.category] = allowed.get(it.category, ZERO) + value
    for cat, cap in terms.get("category_caps", {}).items():
        limit = money(cap["amount"])
        if allowed.get(cat, ZERO) > limit:
            excess = allowed[cat] - limit
            w.apply("R22_CATEGORY_LIMIT", f"{cat.replace('_', ' ').capitalize()} above its sub-limit", -excess,
                    cap["clause"], f"{money(allowed[cat])} assessed, sub-limit {limit}")
            r.non_covered += excess
            allowed[cat] = limit
    avg, si = terms.get("average"), money(sum_insured if sum_insured is not None else sum_insured_available)
    if avg and value_at_risk and value_at_risk > si > ZERO:
        cut = money(w.total * (value_at_risk - si) / value_at_risk)
        w.apply("R45_AVERAGE", "Under-insurance (average clause)", -cut, avg["clause"],
                f"pays sum insured {si} / value at risk {money(value_at_risk)} of the loss")
        r.non_covered += cut
    d = terms["deductible"]
    applies = d.get("applies_to")
    base = sum((v for c, v in allowed.items() if c in applies), ZERO) if applies else w.total
    ded = min(money(d["amount"]), max(min(base, w.total), ZERO))
    if ded or not applies:
        w.apply("R30_DEDUCTIBLE", "Deductible", -ded, d["clause"],
                f"{money(d['amount'])} per claim" + (f" on {', '.join(applies)}" if applies else ""))
    r.deductible = ded
    _cap(w, r, sum_insured_available, terms.get("max_liability_clause"), "Available sum insured")
    r.non_covered, r.depreciation = money(r.non_covered), money(r.depreciation)
    r.payable = max(w.total, ZERO)
    return r


WEEKS = re.compile(r"(\d+)\s*weeks?", re.I)


def benefit_entitlement(item: LineItem, benefit: dict, sum_insured: Decimal) -> tuple[Decimal, str]:
    """Contractual amount for one scheduled benefit (personal accident and life), with how it was worked out."""
    si = money(sum_insured)
    basis = benefit["basis"]
    if basis == "percent_of_si":
        pct = Decimal(str(benefit["percent"]))
        return money(si * pct / 100), f"{pct}% of sum insured {si}"
    if basis == "schedule":
        d = item.description.lower()
        row = next((x for x in benefit["schedule"] if any(k in d for k in x["keywords"])), None)
        if row is None:
            return ZERO, "injury not in the schedule; needs a medical board assessment"
        pct = Decimal(str(row["percent"]))
        return money(si * pct / 100), f"{row['keywords'][0]}: {pct}% of sum insured {si}"
    if basis == "weekly":
        m = WEEKS.search(item.description)
        if not m:
            return ZERO, "number of weeks not stated"
        weeks = min(int(m.group(1)), int(benefit["max_weeks"]))
        weekly = min(money(si * Decimal(str(benefit["percent"])) / 100), money(benefit["weekly_cap"]))
        return money(weekly * weeks), f"{weeks} weeks x {weekly} a week"
    if basis == "reimbursement":
        cap = money(si * Decimal(str(benefit["percent"])) / 100)
        return min(item.amount, cap), f"actual {item.amount}, limit {benefit['percent']}% of sum insured = {cap}"
    raise ValueError(f"unknown benefit basis {basis}")


def adjudicate_benefits(items: list[LineItem], claimed: Decimal, terms: dict, sum_insured_available: Decimal,
                        sum_insured: Decimal) -> Adjudication:
    """Scheduled benefits (personal accident and life): each claimed benefit is replaced by the amount the
    schedule fixes, which can be more or less than the amount written on the claim."""
    r, w = _start(items, claimed)
    benefits = terms["benefits"]
    for it in items:
        b = benefits.get(it.category)
        if b is None:
            w.apply("R10_NOT_COVERED", f"Not a scheduled benefit: {it.description}", -it.amount,
                    terms.get("coverage_clause"), f"category '{it.category}'")
            r.non_covered += it.amount
            continue
        entitled, how = benefit_entitlement(it, b, sum_insured)
        if entitled != it.amount:
            w.apply("R25_BENEFIT_SCHEDULE", f"{it.description}: scheduled benefit {entitled}", entitled - it.amount,
                    b["clause"], how)
            if entitled < it.amount:
                r.non_covered += it.amount - entitled
    d = terms["deductible"]
    ded = min(money(d["amount"]), max(w.total, ZERO))
    if ded:
        w.apply("R30_DEDUCTIBLE", "Deductible", -ded, d["clause"], f"{money(d['amount'])} per claim")
    r.deductible = ded
    _cap(w, r, sum_insured_available, terms.get("max_liability_clause"), "Available sum insured")
    r.non_covered = money(r.non_covered)
    r.payable = max(w.total, ZERO)
    return r


def _cap(w: _Waterfall, r: Adjudication, cap: Decimal, clause: str | None, label: str) -> None:
    cap = money(cap)
    if w.total > cap:
        w.apply("R50_MAX_LIABILITY", f"Capped at {label.lower()}", cap - w.total, clause, f"{label} {cap}")
    else:
        r.steps.append(Step("R50_MAX_LIABILITY", f"Within {label.lower()}", ZERO, w.total, clause, f"{label} {cap}"))
