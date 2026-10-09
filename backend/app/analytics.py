"""Dashboard analytics and the synthetic-portfolio evaluation of the risk rules."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache

from sqlalchemy.orm import Session

from . import sla
from .agents.risk import level, score_features
from .config import settings
from .models import AnalysisRun, Claim, ClaimDecision, PolicyVersion, WorkflowTask


def _latest_ai(db: Session) -> dict[int, ClaimDecision]:
    out: dict[int, ClaimDecision] = {}
    for d in db.query(ClaimDecision).filter_by(source="AI").order_by(ClaimDecision.id).all():
        out[d.claim_id] = d
    return out


LINES = ("health", "motor")
AGE_BUCKETS = ((2, "0-2 days"), (7, "3-7 days"), (14, "8-14 days"), (30, "15-30 days"), (None, "Over 30 days"))
WEEKS = 8


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def dashboard(db: Session, line: str | None = None, days: int | None = None, today: date | None = None) -> dict:
    """Portfolio KPIs for the dashboard. `line` limits to health or motor; `days` to claims filed in that window."""
    now = datetime.now(timezone.utc)
    today = today or now.date()
    claims = db.query(Claim).order_by(Claim.id).all()
    if line in LINES:
        claims = [c for c in claims if c.claim_type == line]
    if days:
        since = now - timedelta(days=days)
        claims = [c for c in claims if _utc(c.created_at) >= since]
    ids = {c.id for c in claims}
    ai = {k: v for k, v in _latest_ai(db).items() if k in ids}
    human = [d for d in db.query(ClaimDecision).filter_by(source="HUMAN").order_by(ClaimDecision.id).all() if d.claim_id in ids]
    runs = [r for r in db.query(AnalysisRun).filter_by(status="SUCCEEDED").order_by(AnalysisRun.id).all() if r.claim_id in ids]
    latest_run: dict[int, AnalysisRun] = {r.claim_id: r for r in runs}
    results = {cid: r.result for cid, r in latest_run.items() if r.result}
    risk = Counter(res["risk"]["level"] for res in results.values())
    durations = [(r.finished_at - r.started_at).total_seconds() * 1000 for r in runs if r.finished_at]
    claimed = sum((Decimal(c.claimed_amount or 0) for c in claims), Decimal(0))
    recommended = sum((Decimal(d.payable_amount or 0) for d in ai.values()), Decimal(0))
    last_human: dict[int, ClaimDecision] = {d.claim_id: d for d in human}
    # override rate is measured on decisions; an escalation hands the claim up rather than disagreeing with the AI
    final = {cid: h for cid, h in last_human.items() if h.decision != "ESCALATE" and cid in ai}
    agree = sum(1 for cid, h in final.items() if _agrees(ai[cid].decision, h.decision))
    amount_overrides = sum(1 for cid, h in final.items() if h.decision == "APPROVE" and h.payable_amount is not None
                           and ai[cid].payable_amount is not None and Decimal(h.payable_amount) != Decimal(ai[cid].payable_amount))
    reviewed = {d.claim_id for d in human}
    escalated = {d.claim_id for d in human if d.decision == "ESCALATE"}
    open_tasks = [t for t in db.query(WorkflowTask).filter_by(status="OPEN").all() if t.claim_id in ids]
    terms = {v.id: v.terms for v in db.query(PolicyVersion).all()}
    clocks: Counter = Counter()
    clock_of: dict[int, dict] = {}
    for c in claims:
        run = latest_run.get(c.id)
        clock_of[c.id] = sla.settlement_clock(c, terms.get(run.policy_version_id) if run else None, last_human.get(c.id), today)
        clocks[clock_of[c.id]["state"]] += 1
    approved = [h for h in last_human.values() if h.decision == "APPROVE"]
    paid = sum((Decimal(h.payable_amount or 0) for h in approved), Decimal(0))
    closed = [c for c in claims if c.status in sla.CLOSED and c.id in last_human]
    turnaround = [(_utc(last_human[c.id].created_at) - _utc(c.created_at)).total_seconds() / 86400 for c in closed]
    by_line_amounts = {}
    for ln in LINES:
        cs = [c for c in claims if c.claim_type == ln]
        by_line_amounts[ln] = {
            "claims": len(cs), "claimed": str(sum((Decimal(c.claimed_amount or 0) for c in cs), Decimal(0))),
            "ai_payable": str(sum((Decimal(ai[c.id].payable_amount or 0) for c in cs if c.id in ai), Decimal(0))),
            "approved": str(sum((Decimal(last_human[c.id].payable_amount or 0) for c in cs
                                 if c.id in last_human and last_human[c.id].decision == "APPROVE"), Decimal(0)))}
    return {
        "filters": {"line": line if line in LINES else None, "days": days or None},
        "totals": {"claims": len(claims), "pending_review": sum(1 for c in claims if c.status in ("PENDING_REVIEW", "ESCALATED")),
                   "high_risk": risk.get("HIGH", 0), "decided": len(last_human),
                   "claimed_amount": str(claimed), "recommended_payable": str(recommended), "approved_amount": str(paid),
                   "avg_analysis_ms": round(sum(durations) / len(durations)) if durations else None,
                   "avg_days_to_decision": round(sum(turnaround) / len(turnaround), 1) if turnaround else None,
                   "overdue": clocks.get("OVERDUE", 0) + clocks.get("BREACHED", 0)},
        "by_status": dict(Counter(c.status for c in claims)),
        "by_recommendation": dict(Counter(d.decision for d in ai.values())),
        "by_risk": dict(risk),
        "by_line": dict(Counter(c.claim_type for c in claims)),
        "by_line_amounts": by_line_amounts,
        "queues": dict(Counter(t.queue for t in open_tasks)),
        "workload": dict(Counter(t.assignee or "Unassigned" for t in open_tasks)),
        "settlement": dict(clocks),
        "ageing": _ageing([c for c in claims if c.status not in sla.CLOSED], today),
        "trend": _trend(claims, last_human, today),
        "top_reasons": _top_reasons(results.values()),
        "risk_signals": dict(Counter(s["code"] for res in results.values() for s in res["risk"]["signals"]).most_common(8)),
        "attention": _attention(claims, clock_of, results, today),
        "human_vs_ai": {"decided": len(final), "agreed": agree, "overridden": len(final) - agree,
                        "amount_overridden": amount_overrides,
                        "override_rate": round((len(final) - agree) / len(final), 3) if final else None,
                        "reviewed": len(reviewed), "escalated": len(escalated),
                        "escalation_rate": round(len(escalated) / len(reviewed), 3) if reviewed else None},
        "human_outcomes": dict(Counter(h.decision for h in last_human.values())),
        "portfolio": portfolio_evaluation(),
    }


def _ageing(open_claims: list[Claim], today: date) -> dict:
    out = {label: 0 for _, label in AGE_BUCKETS}
    for c in open_claims:
        age = (today - _utc(c.created_at).date()).days
        out[next(label for upto, label in AGE_BUCKETS if upto is None or age <= upto)] += 1
    return out


def _trend(claims: list[Claim], last_human: dict[int, ClaimDecision], today: date) -> list[dict]:
    """Claims filed and claims finally decided per week, oldest week first, ending with the current week."""
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=WEEKS - 1)
    weeks = [{"week": (start + timedelta(weeks=i)).isoformat(), "filed": 0, "decided": 0, "claimed": Decimal(0),
              "approved": Decimal(0)} for i in range(WEEKS)]

    def slot(dt: datetime) -> dict | None:
        i = (_utc(dt).date() - start).days // 7
        return weeks[i] if 0 <= i < WEEKS else None

    for c in claims:
        if w := slot(c.created_at):
            w["filed"] += 1
            w["claimed"] += Decimal(c.claimed_amount or 0)
        h = last_human.get(c.id)
        if h and h.decision in ("APPROVE", "REJECT") and (w := slot(h.created_at)):
            w["decided"] += 1
            w["approved"] += Decimal(h.payable_amount or 0) if h.decision == "APPROVE" else Decimal(0)
    return [{**w, "claimed": str(w["claimed"]), "approved": str(w["approved"])} for w in weeks]


def _top_reasons(results) -> list[dict]:
    """Why claims are declined or held: the failing or missing coverage check, with the clause it cites."""
    seen: Counter = Counter()
    clause: dict[str, str | None] = {}
    for res in results:
        for f in res["coverage"]["findings"]:
            if f["outcome"] in ("FAIL", "MISSING"):
                seen[f["code"]] += 1
                clause.setdefault(f["code"], (f.get("citation") or {}).get("clause_ref"))
    return [{"code": k, "count": n, "clause_ref": clause[k]} for k, n in seen.most_common(8)]


def _attention(claims: list[Claim], clock_of: dict[int, dict], results: dict[int, dict], today: date) -> list[dict]:
    """Open claims a supervisor should look at first: past the settlement date, escalated, or high risk."""
    rows = []
    for c in claims:
        if c.status in sla.CLOSED:
            continue
        clock, res = clock_of[c.id], results.get(c.id)
        reasons = []
        if clock["state"] == "OVERDUE":
            reasons.append(f"Settlement {-clock['days_left']} days overdue")
        elif clock["state"] == "DUE_SOON":
            reasons.append(f"Settlement due in {clock['days_left']} days")
        if c.status == "ESCALATED":
            reasons.append("Escalated to a supervisor")
        if res and res["risk"]["level"] == "HIGH":
            reasons.append(f"High risk ({res['risk']['score']})")
        if reasons:
            rank = (clock["days_left"] if clock["days_left"] is not None else 99) - 20 * (c.status == "ESCALATED")
            rows.append({"claim_number": c.claim_number, "claimant_name": c.claimant_name, "claim_type": c.claim_type,
                         "status": c.status, "claimed_amount": str(c.claimed_amount) if c.claimed_amount is not None else None,
                         "age_days": (today - _utc(c.created_at).date()).days, "reasons": reasons, "_rank": rank})
    rows.sort(key=lambda r: r.pop("_rank"))
    return rows[:8]


def _agrees(ai: str, human: str) -> bool:
    return {"APPROVE": "APPROVE", "PARTIAL_APPROVAL": "APPROVE", "RECOMMEND_REJECT": "REJECT",
            "REQUEST_INFO": "REQUEST_INFO", "INVESTIGATE": "INVESTIGATE"}.get(ai) == human


@lru_cache(maxsize=1)
def portfolio_evaluation() -> dict | None:
    """Score the 1,000-claim synthetic portfolio with the live risk rules and compare to injected labels.

    This measures how well the transparent rules recover patterns we injected ourselves; it is not a
    claim about real-world fraud detection performance.
    """
    path = settings.data_dir / "synthetic" / "claims_portfolio.csv"
    if not path.exists():
        return None
    tp = fp = fn = tn = 0
    levels: Counter = Counter()
    by_line: Counter = Counter()
    amounts: list[float] = []
    for row in csv.DictReader(path.open(encoding="utf-8")):
        claimed, total = float(row["claimed_amount"]), float(row["document_total"])
        score, _ = score_features({
            "amount_ratio": claimed / float(row["sum_insured"]), "days_since_start": int(row["days_since_policy_start"]),
            "prior_claims": int(row["prior_claims_12m"]),
            "duplicate_of": "match" if row["duplicate_match"] == "1" else None,
            "amount_gap": abs(claimed - total) / total if total else 0,
        })
        lv = level(score)
        levels[lv] += 1
        by_line[row["line_of_business"]] += 1
        amounts.append(claimed)
        flagged, label = lv != "LOW", row["fraud_label"] == "1"
        tp += flagged and label
        fp += flagged and not label
        fn += (not flagged) and label
        tn += (not flagged) and (not label)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {"claims": sum(levels.values()), "by_risk": dict(levels), "by_line": dict(by_line),
            "injected_anomalies": tp + fn, "flagged": tp + fp,
            "precision": round(precision, 3), "recall": round(recall, 3),
            "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "median_claim": sorted(amounts)[len(amounts) // 2],
            "note": "Synthetic portfolio with injected patterns; measures rule recall of injected patterns only."}
