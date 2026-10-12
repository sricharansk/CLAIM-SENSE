#!/usr/bin/env python3
"""Run every claim packet in the repository through Claim Sense and report the results.

Usage: python scripts/claims_report.py [--out reports]

Creates a temporary SQLite database seeded with the synthetic corpus (the 34 seeded claims are analysed on
start-up), then files the 7 evaluation packets and the demo upload as new claims through the real API, exactly
as the UI does. Every figure in claims_results.json and claims_results.md is read back from the API: amounts from
the deterministic rules engine, clauses from the matched wording, routing from the review queue. Also includes the
risk-rule results on the 1,000-claim synthetic portfolio. Synthetic data only; the LLM is off.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES = ["health", "motor", "property", "travel"]
DEDUCTIONS = {
    "R10_NON_PAYABLE": "Not payable", "R15_DEPRECIATION": "Depreciation", "R20_PER_DAY_LIMIT": "Per-day limit",
    "R20_ITEM_LIMIT": "Per-item limit", "R20_BENEFIT_LIMIT": "Benefit limit", "R25_UNDERINSURANCE": "Underinsurance",
    "R30_DEDUCTIBLE": "Deductible / excess", "R40_COPAY": "Co-payment", "R50_MAX_LIABILITY": "Sum insured cap",
    "R99_NOT_ADMISSIBLE": "Not admissible",
}


def _ok(r, what: str):
    if r.status_code >= 400:
        raise RuntimeError(f"{what} failed with HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def _file_packet(client, folder: Path, policy_number: str, claim_type: str, claimant: str, title: str) -> str:
    n = _ok(client.post("/api/v1/claims", json={"policy_number": policy_number, "claim_type": claim_type,
                                                 "claimant_name": claimant, "description": title}), "create claim")["claim_number"]
    files = [("files", (p.name, p.read_bytes(), "text/plain")) for p in sorted(folder.glob("*.txt"))]
    _ok(client.post(f"/api/v1/claims/{n}/documents", files=files), "upload documents")
    _ok(client.post(f"/api/v1/claims/{n}/analyze"), "analyse claim")
    return n


def _row(client, number: str, source: str, queues: dict[str, str]) -> dict:
    claim = _ok(client.get(f"/api/v1/claims/{number}"), "read claim")
    res = _ok(client.get(f"/api/v1/claims/{number}/analysis"), "read analysis")["result"]
    adj, cov, risk, rec = res["adjudication"], res["coverage"], res["risk"], res["recommendation"]
    fail = next((f for f in cov["findings"] if f["outcome"] == "FAIL"), None)
    deductions: dict[str, Decimal] = defaultdict(Decimal)
    for s in adj["waterfall"]:
        if s["rule_id"] in DEDUCTIONS and Decimal(s["adjustment"]) != 0:
            deductions[s["rule_id"]] += Decimal(s["adjustment"])
    return {
        "claim_number": number, "source": source, "line": claim["claim_type"], "claimant": claim["claimant_name"],
        "policy_number": res["policy"]["policy_number"], "product": f"{res['policy']['product_code']} v{res['policy']['version']}",
        "incident_date": res["facts"].get("incident_date"), "documents": len(claim["documents"]),
        "claimed": adj["claimed_amount"], "billed": adj["gross_billed"], "payable": adj["payable_amount"],
        "deductions": {k: f"{v:.2f}" for k, v in deductions.items()},
        "coverage": cov["status"],
        "failing_check": {"code": fail["code"], "clause_ref": (fail.get("citation") or {}).get("clause_ref"),
                          "message": fail["message"]} if fail else None,
        "missing_documents": cov["missing_documents"],
        "risk_level": risk["level"], "risk_score": risk["score"], "risk_signals": [s["code"] for s in risk["signals"]],
        "recommendation": rec["decision"], "queue": queues.get(number),
        "evidence_items": len(res["evidence"]),
        "policy_clauses_cited": sorted({e["clause_ref"] for e in res["evidence"] if e["kind"] == "policy_clause"}),
    }


def build(client) -> dict:
    from app.config import settings

    seeded = [c["claim_number"] for c in _ok(client.get("/api/v1/claims"), "list claims")]
    filed: list[tuple[str, str]] = []
    for case in json.loads((settings.data_dir / "evaluation" / "golden_cases.json").read_text())["claims"]:
        if "packet" in case:
            folder = settings.data_dir / "evaluation" / "packets" / case["packet"]
            filed.append((_file_packet(client, folder, case["policy_number"], case["claim_type"], case["claimant"], case["title"]),
                          f"evaluation packet {case['packet']}"))
    filed.append((_file_packet(client, settings.data_dir / "claims" / "demo_upload", "CS-HLT-23-000089", "health",
                               "Fatima Shaikh", "Demo upload: kidney stone"), "demo upload packet"))
    queues = {t["claim_number"]: t["queue"] for t in _ok(client.get("/api/v1/reviews"), "review queue")}
    rows = [_row(client, n, "seeded scenario", queues) for n in seeded] + [_row(client, n, s, queues) for n, s in filed]
    rows.sort(key=lambda r: (LINES.index(r["line"]), r["claim_number"]))

    by_line = {}
    for line in LINES:
        rs = [r for r in rows if r["line"] == line]
        billed = sum(Decimal(r["billed"]) for r in rs)
        payable = sum(Decimal(r["payable"]) for r in rs)
        by_line[line] = {"claims": len(rs), "billed": f"{billed:.2f}", "payable": f"{payable:.2f}",
                         "payout_ratio": round(float(payable / billed), 3) if billed else None,
                         "recommendations": dict(Counter(r["recommendation"] for r in rs))}
    billed = sum(Decimal(r["billed"]) for r in rows)
    payable = sum(Decimal(r["payable"]) for r in rows)
    deductions: dict[str, Decimal] = defaultdict(Decimal)
    for r in rows:
        for k, v in r["deductions"].items():
            deductions[k] += Decimal(v)
    analytics = _ok(client.get("/api/v1/analytics"), "analytics")
    evaluation = json.loads((ROOT / "reports" / "evaluation.json").read_text())["summary"] \
        if (ROOT / "reports" / "evaluation.json").exists() else None
    return {
        "report": "Claim Sense results on every claim packet", "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": "synthetic only", "llm": "off (deterministic rules and extractive retrieval)",
        "rules_version": settings.rules_version, "risk_version": settings.risk_version,
        "summary": {
            "claims": len(rows), "billed": f"{billed:.2f}", "payable": f"{payable:.2f}",
            "payout_ratio": round(float(payable / billed), 3) if billed else None,
            "recommendations": dict(Counter(r["recommendation"] for r in rows)),
            "coverage": dict(Counter(r["coverage"] for r in rows)),
            "risk": dict(Counter(r["risk_level"] for r in rows)),
            "queues": dict(Counter(r["queue"] for r in rows)),
            "deductions": {k: f"{v:.2f}" for k, v in sorted(deductions.items())},
            "human_review_required": all(r["queue"] for r in rows),
        },
        "by_line": by_line, "claims": rows,
        "portfolio_risk_rules": analytics.get("portfolio"),
        "golden_evaluation": evaluation,
    }


def _inr(x) -> str:
    v = Decimal(str(x))
    return f"₹{v:,.0f}" if v == v.to_integral() else f"₹{v:,.2f}"


def to_markdown(r: dict) -> str:
    s = r["summary"]
    out = [
        "# Claim Sense results on every claim packet", "",
        f"Generated {r['generated_at']} by `python scripts/claims_report.py` on a fresh database. Synthetic data only; "
        f"LLM {r['llm']}. Rules {r['rules_version']}, risk {r['risk_version']}. Every figure is read back from the API.", "",
        f"**{s['claims']} claims** across health, motor, property and travel: {_inr(s['billed'])} billed, "
        f"{_inr(s['payable'])} recommended payable ({s['payout_ratio']:.1%}). Every claim was routed to a human review queue; "
        "no claim was decided by the system.", "",
        "## By line of business", "", "| Line | Claims | Billed | Payable | Payout | Recommendations |", "|---|---|---|---|---|---|",
    ]
    for line, b in r["by_line"].items():
        recs = ", ".join(f"{k.replace('_', ' ').lower()} {v}" for k, v in sorted(b["recommendations"].items()))
        out.append(f"| {line.title()} | {b['claims']} | {_inr(b['billed'])} | {_inr(b['payable'])} | "
                   f"{b['payout_ratio']:.1%} | {recs} |")
    out += ["", "## Outcomes", "", "| Recommendation | Claims |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(s["recommendations"].items())]
    out += ["", "| Risk level | Claims |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(s["risk"].items())]
    out += ["", "| Review queue | Claims |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(s["queues"].items())]
    out += ["", "## Where the money went", "", "Total reductions from billed to payable, by rule:", "", "| Rule | Amount |", "|---|---|"]
    out += [f"| {DEDUCTIONS[k]} (`{k}`) | {_inr(-Decimal(v))} |" for k, v in s["deductions"].items()]
    out += ["", "## Every claim", "",
            "| Claim | Line | Policy wording | Billed | Payable | Coverage | Reason / clause | Risk | Recommendation | Queue |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for c in r["claims"]:
        if c["failing_check"]:
            reason = f"{c['failing_check']['code']} §{c['failing_check']['clause_ref']}"
        elif c["missing_documents"]:
            reason = "missing " + ", ".join(c["missing_documents"])
        else:
            reason = ", ".join(DEDUCTIONS[k].lower() for k in c["deductions"]) or "none"
        risk = c["risk_level"] + (f" ({', '.join(c['risk_signals'])})" if c["risk_signals"] else "")
        out.append(f"| {c['claim_number']} | {c['line']} | {c['product']} | {_inr(c['billed'])} | {_inr(c['payable'])} | "
                   f"{c['coverage']} | {reason} | {risk} | {c['recommendation']} | {c['queue']} |")
    p = r.get("portfolio_risk_rules")
    if p:
        out += ["", "## Risk rules on the 1,000-claim synthetic portfolio", "",
                f"{p['claims']} synthetic claims ({', '.join(f'{k} {v}' for k, v in p['by_line'].items())}) with "
                f"{p['injected_anomalies']} injected anomaly patterns. The transparent risk rules flagged {p['flagged']}: "
                f"precision {p['precision']:.1%}, recall {p['recall']:.1%} "
                f"(TP {p['confusion']['tp']}, FP {p['confusion']['fp']}, FN {p['confusion']['fn']}, TN {p['confusion']['tn']}). "
                f"{p['note']}"]
    e = r.get("golden_evaluation")
    if e:
        out += ["", "## Golden evaluation", "",
                f"{e['checks_passed']} of {e['checks']} checks passed across {e['claim_cases']} hand-worked claim cases and "
                f"{e['questions']} policy-assistant questions (retrieval hit@1 {e['retrieval_hit_at_1']:.0%}). "
                "See `reports/evaluation.md`."]
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "reports"), help="output directory (default: reports/)")
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="claimsense-report-"))
    os.environ.update(DATABASE_URL=f"sqlite:///{tmp / 'report.db'}", CLAIMSENSE_STORAGE_DIR=str(tmp / "storage"),
                      CLAIMSENSE_SEED="true", CLAIMSENSE_SEED_PACKETS="false")
    os.environ.pop("ANTHROPIC_API_KEY", None)
    sys.path.insert(0, str(ROOT / "backend"))

    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import app

    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"username": "supervisor", "password": settings.demo_password})
        r.raise_for_status()
        client.headers["Authorization"] = f"Bearer {r.json()['token']}"
        report = build(client)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "claims_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "claims_results.md").write_text(to_markdown(report), encoding="utf-8")
    s = report["summary"]
    print(f"{s['claims']} claims, billed {s['billed']}, payable {s['payable']} ({s['payout_ratio']:.1%}); "
          f"recommendations {s['recommendations']}")
    print(f"wrote {out / 'claims_results.json'} and {out / 'claims_results.md'}")
    return 0 if s["human_review_required"] else 1


if __name__ == "__main__":
    sys.exit(main())
