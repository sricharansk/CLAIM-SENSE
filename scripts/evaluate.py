#!/usr/bin/env python3
"""Run the Claim Sense golden evaluation on a fresh, isolated database.

Usage: python scripts/evaluate.py [--out reports]

Creates a temporary SQLite database seeded with the synthetic corpus, runs the 12 claim cases and 21
policy-assistant questions in data/evaluation/ through the real API, and writes evaluation.json and
evaluation.md. Exits 1 if any check fails. The LLM is always off so results are deterministic.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "reports"), help="output directory (default: reports/)")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="claimsense-eval-"))
    os.environ.update(DATABASE_URL=f"sqlite:///{tmp / 'eval.db'}", CLAIMSENSE_STORAGE_DIR=str(tmp / "storage"),
                      CLAIMSENSE_SEED="true")
    os.environ.pop("ANTHROPIC_API_KEY", None)
    sys.path.insert(0, str(ROOT / "backend"))

    from fastapi.testclient import TestClient

    from app import evaluation
    from app.config import settings
    from app.main import app

    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"username": "supervisor", "password": settings.demo_password})
        r.raise_for_status()
        client.headers["Authorization"] = f"Bearer {r.json()['token']}"
        report = evaluation.run(client)
    j, m = evaluation.write(report, Path(args.out))
    s = report["summary"]
    for d in report["dimensions"].values():
        print(f"  {d['label']:<24} {d['passed']:>3} / {d['total']:<3}")
    print(f"claim cases {s['claim_cases_passed']}/{s['claim_cases']}, questions {s['questions_passed']}/{s['questions']}, "
          f"checks {s['checks_passed']}/{s['checks']}; hit@1 {s['retrieval_hit_at_1']}, MRR {s['mean_reciprocal_rank']}")
    for item in report["claims"] + report["questions"]:
        for c in item["checks"]:
            if not c["passed"]:
                print(f"FAIL {item['id']} {c['dimension']} / {c['check']}: expected {c['expected']!r}, got {c['actual']!r}")
    print(f"wrote {j} and {m}")
    return 0 if s["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
