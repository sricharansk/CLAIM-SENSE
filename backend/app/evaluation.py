"""Golden evaluation suite (blueprint Prompt 17).

Runs the real API on the golden claims and policy questions in data/evaluation/ and scores the results along
seven dimensions. Expected values are worked out by hand from the synthetic wording; this module only compares.
It talks to the app through an HTTP client (FastAPI TestClient from scripts/evaluate.py), so it exercises the
same endpoints as the UI. It never feeds back into claim decisions.
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, settings

EVAL_DIR = REPO_ROOT / "data" / "evaluation"
REQUIRED_CATEGORIES = ["clearly_covered", "excluded", "partial_coverage", "insufficient_evidence", "high_risk",
                       "deductible", "sub_limit", "max_coverage", "duplicate", "ambiguous_policy_version"]
DIMENSIONS = {
    "retrieval": "Retrieval correctness",
    "citation": "Citation correctness",
    "groundedness": "Groundedness",
    "coverage": "Coverage state",
    "adjudication": "Adjudication amount",
    "risk": "Risk classification",
    "workflow": "Workflow outcome",
}
QUOTE_RE = re.compile(r"(.+?) \[([A-Z-]+) v([\w.]+) §([\w.]+), p\.(\d+)\]\s*")


class _Case:
    def __init__(self, case_id: str):
        self.id, self.checks = case_id, []

    def check(self, dimension: str, name: str, expected: Any, actual: Any, passed: bool | None = None) -> None:
        ok = (expected == actual) if passed is None else passed
        self.checks.append({"dimension": dimension, "check": name, "expected": expected, "actual": actual, "passed": bool(ok)})

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)


def _ok(r, what: str) -> Any:
    if r.status_code >= 400:
        raise RuntimeError(f"{what} failed with HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def _clause_index(client) -> dict[int, dict]:
    out = {}
    for p in _ok(client.get("/api/v1/policies"), "list policies"):
        for v in _ok(client.get(f"/api/v1/policies/{p['product_code']}/versions"), "policy versions"):
            for c in v["clauses"]:
                out[c["id"]] = {"product_code": p["product_code"], "version": v["version"], "clause_ref": c["clause_ref"],
                                "text": c["text"]}
    return out


def _create_from_packet(client, case: dict) -> str:
    n = _ok(client.post("/api/v1/claims", json={"policy_number": case["policy_number"], "claim_type": case["claim_type"],
                                                 "claimant_name": case["claimant"], "description": case["title"]}),
            "create claim")["claim_number"]
    folder = EVAL_DIR / "packets" / case["packet"]
    files = [("files", (p.name, p.read_bytes(), "text/plain")) for p in sorted(folder.glob("*.txt"))]
    _ok(client.post(f"/api/v1/claims/{n}/documents", files=files), "upload documents")
    _ok(client.post(f"/api/v1/claims/{n}/analyze"), "analyse claim")
    return n


def _waterfall_totals(steps: list[dict]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for s in steps:
        totals[s["rule_id"]] += Decimal(s["adjustment"])
    return totals


def evaluate_claim(client, case: dict, clauses: dict[int, dict], queues: dict[str, str] | None = None) -> dict:
    t = time.perf_counter()
    number = case.get("claim_number") or _create_from_packet(client, case)
    analysis = _ok(client.get(f"/api/v1/claims/{number}/analysis"), "read analysis")
    res, exp = analysis["result"], case["expect"]
    k = _Case(case["id"])
    version = res["policy"]["version"]
    k.check("retrieval", "policy version in force", exp["policy_version"], version)
    if "retrieved_clause" in exp:
        refs = [h["clause_ref"] for h in res.get("retrieval", [])]
        k.check("retrieval", "relevant clause retrieved", exp["retrieved_clause"], refs, exp["retrieved_clause"] in refs)

    cov = res["coverage"]
    k.check("coverage", "coverage status", exp["coverage_status"], cov["status"])
    fail = next((f for f in cov["findings"] if f["outcome"] == "FAIL"), None)
    if "failing_check" in exp:
        want = exp["failing_check"]
        k.check("coverage", "failing check", want["code"] if want else None, fail["code"] if fail else None)
        if want:
            got = (fail.get("citation") or {}).get("clause_ref") if fail else None
            k.check("citation", "failing check cites clause", want["clause_ref"], got)
    if "missing_documents" in exp:
        k.check("coverage", "missing documents", exp["missing_documents"], cov["missing_documents"])

    # every clause the evidence package or the waterfall relies on must exist, in the matched wording, word for word
    bad = []
    for e in res["evidence"]:
        if "clause_id" in e:
            c = clauses.get(e["clause_id"])
            if c is None or c["text"] != e["text"] or c["clause_ref"] != e["clause_ref"]:
                bad.append(f"evidence {e.get('clause_ref')}")
            elif e["kind"] == "policy_clause" and c["version"] != version:
                bad.append(f"evidence {e['clause_ref']} from v{c['version']}")
    version_refs = {c["clause_ref"] for c in clauses.values() if c["version"] == version
                    and c["product_code"] == res["policy"]["product_code"]}
    for s in res["adjudication"]["waterfall"]:
        if s.get("clause_ref") and s["clause_ref"] not in version_refs:
            bad.append(f"waterfall {s['rule_id']} §{s['clause_ref']}")
    k.check("groundedness", "evidence and waterfall clauses resolve to the matched wording", [], bad)

    adj = res["adjudication"]
    k.check("adjudication", "payable amount", exp["payable_amount"], adj["payable_amount"])
    totals = _waterfall_totals(adj["waterfall"])
    for rule, amount in exp.get("waterfall", {}).items():
        want = Decimal(amount) if amount is not None else Decimal("0")
        k.check("adjudication", f"waterfall {rule}", f"{want:.2f}", f"{totals.get(rule, Decimal('0')):.2f}")

    risk = res["risk"]
    k.check("risk", "risk level", exp["risk_level"], risk["level"])
    if "risk_signals" in exp:
        codes = sorted(s["code"] for s in risk["signals"])
        k.check("risk", "risk signals present", sorted(exp["risk_signals"]), codes, set(exp["risk_signals"]) <= set(codes))

    rec = res["recommendation"]
    k.check("workflow", "recommendation", exp["recommendation"], rec["decision"])
    k.check("workflow", "human review required", True, rec.get("requires_human_review"))
    if queues is None:
        queues = {t["claim_number"]: t["queue"] for t in _ok(client.get("/api/v1/reviews"), "review queue")}
    k.check("workflow", "routed to queue", exp["queue"], queues.get(number))
    return {"id": case["id"], "title": case["title"], "categories": case["categories"], "claim_number": number,
            "source": "new packet" if "packet" in case else "seeded scenario", "packet": case.get("packet"),
            "expected": {"recommendation": exp["recommendation"], "payable_amount": exp["payable_amount"]},
            "actual": {"recommendation": rec["decision"], "payable_amount": adj["payable_amount"],
                       "risk_level": risk["level"], "policy_version": version},
            "working": case.get("working"), "passed": k.passed, "checks": k.checks,
            "duration_ms": round((time.perf_counter() - t) * 1000)}


def evaluate_question(client, q: dict, clauses: dict[int, dict]) -> dict:
    body = {"question": q["question"]}
    for key in ("product_code", "version"):
        if q.get(key):
            body[key] = q[key]
    r = _ok(client.post("/api/v1/rag/query", json=body), "policy assistant")
    k = _Case(q["id"])
    refs = [c["clause_ref"] for c in r["citations"]]
    rank = None
    if q.get("expect_refusal"):
        k.check("groundedness", "refuses without evidence", "refusal", r["mode"], not r["grounded"] and r["mode"] == "refusal")
    else:
        k.check("groundedness", "answers from evidence", True, r["grounded"])
        want = q["expect_clause"]
        rank = refs.index(want) + 1 if want in refs else None
        k.check("retrieval", "expected clause in top 3", want, refs[:3], want in refs[:3])
        k.check("citation", "top citation is the expected clause", want, refs[0] if refs else None)
        outside = [c for c in r["citations"] if (q.get("product_code") and c["product_code"] != q["product_code"])
                 or (q.get("version") and c["version"] != q["version"])]
        k.check("citation", "citations stay within the selected policy", [], [f"{c['product_code']} v{c['version']}" for c in outside])
        unresolved = [c["clause_ref"] for c in r["citations"]
                      if clauses.get(c["clause_id"], {}).get("text") != c["text"]]
        k.check("groundedness", "citations resolve to stored clause text", [], unresolved)
        if r["mode"] == "extractive":
            cited = {(c["product_code"], c["version"], c["clause_ref"]): c["text"] for c in r["citations"]}
            quotes = QUOTE_RE.findall(r["answer"])
            ungrounded = [s for s, prod, ver, ref, _ in quotes if s.strip() not in cited.get((prod, ver, ref), "")]
            k.check("groundedness", "every quoted sentence appears in its cited clause", [], ungrounded, bool(quotes) and not ungrounded)
        if q.get("expect_text"):
            k.check("retrieval", "answer contains the key term", q["expect_text"], r["answer"][:160], q["expect_text"] in r["answer"])
        if q.get("expect_versions"):
            versions = sorted({c["version"] for c in r["citations"] if c["clause_ref"] == want})
            k.check("citation", "cites every wording version", q["expect_versions"], versions, set(q["expect_versions"]) <= set(versions))
    scope = " ".join(filter(None, [q.get("product_code"), q.get("version")])) or "all policies"
    return {"id": q["id"], "kind": q["kind"], "question": q["question"], "scope": scope,
            "mode": r["mode"], "top_citation": refs[0] if refs else None, "expected_clause": q.get("expect_clause"),
            "rank": rank, "passed": k.passed, "checks": k.checks}


def run(client) -> dict:
    started = time.perf_counter()
    cases = json.loads((EVAL_DIR / "golden_cases.json").read_text())["claims"]
    questions = json.loads((EVAL_DIR / "rag_questions.json").read_text())["questions"]
    clauses = _clause_index(client)
    claim_results = [evaluate_claim(client, c, clauses) for c in cases]
    rag_results = [evaluate_question(client, q, clauses) for q in questions]

    dims = {d: {"label": label, "passed": 0, "total": 0} for d, label in DIMENSIONS.items()}
    for item in claim_results + rag_results:
        for c in item["checks"]:
            dims[c["dimension"]]["total"] += 1
            dims[c["dimension"]]["passed"] += c["passed"]
    for d in dims.values():
        d["score"] = round(d["passed"] / d["total"], 3) if d["total"] else None
    answerable = [r for r in rag_results if r["expected_clause"]]
    refusals = [r for r in rag_results if not r["expected_clause"]]
    covered = {cat: [c["id"] for c in claim_results if cat in c["categories"]] for cat in REQUIRED_CATEGORIES}
    checks = [c for item in claim_results + rag_results for c in item["checks"]]
    summary = {
        "claim_cases": len(claim_results), "claim_cases_passed": sum(c["passed"] for c in claim_results),
        "questions": len(rag_results), "questions_passed": sum(r["passed"] for r in rag_results),
        "checks": len(checks), "checks_passed": sum(c["passed"] for c in checks),
        "retrieval_hit_at_1": round(sum(r["rank"] == 1 for r in answerable) / len(answerable), 3) if answerable else None,
        "retrieval_hit_at_3": round(sum(bool(r["rank"]) and r["rank"] <= 3 for r in answerable) / len(answerable), 3) if answerable else None,
        "mean_reciprocal_rank": round(sum(1 / r["rank"] for r in answerable if r["rank"]) / len(answerable), 3) if answerable else None,
        "refusal_accuracy": round(sum(r["passed"] for r in refusals) / len(refusals), 3) if refusals else None,
        "required_categories_covered": all(covered.values()),
        "avg_claim_case_ms": round(sum(c["duration_ms"] for c in claim_results) / len(claim_results)) if claim_results else None,
    }
    summary["all_passed"] = summary["checks_passed"] == summary["checks"] and summary["required_categories_covered"]
    return {
        "suite": "Claim Sense golden evaluation", "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rules_version": settings.rules_version, "risk_version": settings.risk_version,
        "llm": "off (extractive answers)", "data": "synthetic only",
        "summary": summary, "dimensions": dims, "categories": covered,
        "claims": claim_results, "questions": rag_results,
        "duration_s": round(time.perf_counter() - started, 2),
    }


def _mark(ok: bool) -> str:
    return "pass" if ok else "**FAIL**"


def to_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# Claim Sense evaluation report", "",
        f"Generated {report['generated_at']} by `python scripts/evaluate.py` on a fresh database with synthetic data only. "
        f"Rules {report['rules_version']}, risk {report['risk_version']}, LLM {report['llm']}.", "",
        f"**Result: {'all checks passed' if s['all_passed'] else 'some checks failed'}.** "
        f"{s['checks_passed']} of {s['checks']} checks passed across {s['claim_cases']} claim cases and {s['questions']} policy questions.", "",
        "## Scorecard", "", "| Dimension | Passed | Score |", "|---|---|---|",
    ]
    for d in report["dimensions"].values():
        lines.append(f"| {d['label']} | {d['passed']} / {d['total']} | {d['score']:.0%} |" if d["total"] else f"| {d['label']} | 0 / 0 | n/a |")
    lines += ["", "| Policy assistant metric | Value |", "|---|---|",
              f"| Retrieval hit@1 | {s['retrieval_hit_at_1']:.0%} |", f"| Retrieval hit@3 | {s['retrieval_hit_at_3']:.0%} |",
              f"| Mean reciprocal rank | {s['mean_reciprocal_rank']:.3f} |", f"| Correct refusals | {s['refusal_accuracy']:.0%} |", "",
              "## Required cases", "", "| Case type | Covered by |", "|---|---|"]
    for cat, ids in report["categories"].items():
        lines.append(f"| {cat.replace('_', ' ')} | {', '.join(ids) or '**missing**'} |")
    lines += ["", "## Claim cases", "", "| Case | Claim | What it tests | Recommendation (expected / actual) | Payable (expected / actual) | Result |",
              "|---|---|---|---|---|---|"]
    for c in report["claims"]:
        e, a = c["expected"], c["actual"]
        lines.append(f"| {c['id']} | {c['packet'] or c['claim_number']} | {c['title']} | {e['recommendation']} / {a['recommendation']} | "
                     f"{e['payable_amount']} / {a['payable_amount']} | {_mark(c['passed'])} |")
    lines += ["", "## Policy assistant questions", "", "| Q | Kind | Question | Scope | Expected / top citation | Mode | Result |",
              "|---|---|---|---|---|---|---|"]
    for q in report["questions"]:
        exp = f"§{q['expected_clause']} / §{q['top_citation']}" if q["expected_clause"] else "refusal / " + q["mode"]
        lines.append(f"| {q['id']} | {q['kind']} | {q['question']} | {q['scope']} | {exp} | {q['mode']} | {_mark(q['passed'])} |")
    failed = [(item["id"], c) for item in report["claims"] + report["questions"] for c in item["checks"] if not c["passed"]]
    lines += ["", "## Failed checks", ""]
    if failed:
        lines += [f"- {i} {c['dimension']} / {c['check']}: expected `{c['expected']}`, got `{c['actual']}`" for i, c in failed]
    else:
        lines.append("None.")
    lines += ["", "## Hand-worked expectations", ""]
    lines += [f"- **{c['id']}** ({c['claim_number']}): {c['working']}" for c in report["claims"] if c.get("working")]
    lines.append("")
    return "\n".join(lines)


def write(report: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    j, m = out_dir / "evaluation.json", out_dir / "evaluation.md"
    j.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    m.write_text(to_markdown(report), encoding="utf-8")
    return j, m
