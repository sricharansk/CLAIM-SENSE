"""Dashboard analytics and the synthetic-portfolio evaluation of the risk rules."""
from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal
from functools import lru_cache

from sqlalchemy.orm import Session

from .agents.risk import level, score_features
from .config import settings
from .models import AnalysisRun, Claim, ClaimDecision, WorkflowTask


def _latest_ai(db: Session) -> dict[int, ClaimDecision]:
    out: dict[int, ClaimDecision] = {}
    for d in db.query(ClaimDecision).filter_by(source="AI").order_by(ClaimDecision.id).all():
        out[d.claim_id] = d
    return out


def dashboard(db: Session) -> dict:
    claims = db.query(Claim).all()
    ai = _latest_ai(db)
    human = db.query(ClaimDecision).filter_by(source="HUMAN").all()
    runs = db.query(AnalysisRun).filter_by(status="SUCCEEDED").all()
    latest_run: dict[int, AnalysisRun] = {}
    for r in sorted(runs, key=lambda r: r.id):
        latest_run[r.claim_id] = r
    risk = Counter(r.result["risk"]["level"] for r in latest_run.values() if r.result)
    durations = [(r.finished_at - r.started_at).total_seconds() * 1000 for r in runs if r.finished_at]
    claimed = sum((Decimal(c.claimed_amount or 0) for c in claims), Decimal(0))
    recommended = sum((Decimal(d.payable_amount or 0) for d in ai.values()), Decimal(0))
    last_human: dict[int, ClaimDecision] = {}
    for d in sorted(human, key=lambda d: d.id):
        last_human[d.claim_id] = d
    agree = sum(1 for cid, h in last_human.items() if cid in ai and _agrees(ai[cid].decision, h.decision))
    open_tasks = db.query(WorkflowTask).filter_by(status="OPEN").all()
    return {
        "totals": {"claims": len(claims), "pending_review": sum(1 for c in claims if c.status == "PENDING_REVIEW"),
                   "high_risk": risk.get("HIGH", 0), "decided": len(last_human),
                   "claimed_amount": str(claimed), "recommended_payable": str(recommended),
                   "avg_analysis_ms": round(sum(durations) / len(durations)) if durations else None},
        "by_status": dict(Counter(c.status for c in claims)),
        "by_recommendation": dict(Counter(d.decision for d in ai.values())),
        "by_risk": dict(risk),
        "by_line": dict(Counter(c.claim_type for c in claims)),
        "queues": dict(Counter(t.queue for t in open_tasks)),
        "human_vs_ai": {"decided": len(last_human), "agreed": agree, "overridden": len(last_human) - agree},
        "portfolio": portfolio_evaluation(),
    }


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
