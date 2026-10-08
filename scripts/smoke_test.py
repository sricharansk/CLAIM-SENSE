"""Golden-path smoke test against a running Claim Sense deployment (local, Docker or cloud).

Usage: python scripts/smoke_test.py http://localhost:8080 [password]
Signs in as the synthetic supervisor account (password from the argument, $DEMO_PASSWORD or the
default demo password). Uses only the standard library. Exits non-zero on the first failed check.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/") + "/api/v1"
DEMO = Path(__file__).resolve().parents[1] / "data" / "claims" / "demo_upload"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else os.getenv("DEMO_PASSWORD", "claimsense-demo")
TOKEN: str | None = None


def call(method: str, path: str, body: dict | None = None, files: list[Path] | None = None):
    headers, data = {}, None
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for f in files:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{f.name}"\r\n'
                         f"Content-Type: text/plain\r\n\r\n".encode() + f.read_bytes() + b"\r\n")
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{' - ' + detail if detail else ''}")
    if not ok:
        sys.exit(1)


health = call("GET", "/health")
check("health", health["status"] == "ok", json.dumps(health))
ready = call("GET", "/ready")
check("ready", ready["status"] == "ready" and ready["policy_index"] == "ok", json.dumps(ready))
try:
    call("GET", "/claims")
    check("API requires sign-in", False, "unauthenticated request was accepted")
except urllib.error.HTTPError as e:
    check("API requires sign-in", e.code == 401, f"HTTP {e.code}")
TOKEN = call("POST", "/auth/login", {"username": "supervisor", "password": PASSWORD})["token"]
check("sign in", bool(TOKEN))
claims = call("GET", "/claims")
check("seeded claims", len(claims) >= 8, f"{len(claims)} claims")
c = call("POST", "/claims", {"policy_number": "CS-HLT-23-000089", "claim_type": "health",
                             "claimant_name": "Fatima Shaikh", "description": "smoke test"})
n = c["claim_number"]
check("create claim", n.startswith("CLM-"), n)
docs = call("POST", f"/claims/{n}/documents", files=[DEMO / x for x in ("claim_form.txt", "hospital_bill.txt", "discharge_summary.txt")])
check("upload + extract", {d["doc_type"] for d in docs} == {"claim_form", "hospital_bill", "discharge_summary"},
      ", ".join(f"{d['filename']}={d['facts_extracted']} facts" for d in docs))
a = call("POST", f"/claims/{n}/analyze")
res = a["result"]
check("agent pipeline", a["status"] == "SUCCEEDED" and len(a["agents"]) == 8, f"{len(a['agents'])} agent runs")
check("coverage", res["coverage"]["status"] == "COVERED")
check("adjudication", res["adjudication"]["payable_amount"] == "64080.00", res["adjudication"]["payable_amount"])
# On a re-run the same packet is a duplicate of the previous smoke claim, which must be flagged.
dup = "POSSIBLE_DUPLICATE" in {s["code"] for s in res["risk"]["signals"]}
expected = "INVESTIGATE" if dup else "PARTIAL_APPROVAL"
check("recommendation", res["recommendation"]["decision"] == expected,
      res["recommendation"]["decision"] + (" (duplicate of an earlier smoke-test claim)" if dup else ""))
check("citations", all(e.get("clause_ref") for e in res["evidence"] if e["kind"] == "policy_clause"),
      f"{len(res['evidence'])} evidence items")
r = call("POST", f"/claims/{n}/review", {"action": "APPROVE", "notes": "smoke test"})
check("human review", r["status"] == "APPROVED", json.dumps(r))
audit = call("GET", f"/audit?claim_number={n}")
check("audit trail", {"CLAIM_CREATED", "AI_RECOMMENDATION", "HUMAN_DECISION"} <= {e["event_type"] for e in audit}, f"{len(audit)} events")
q = call("POST", "/rag/query", {"question": "What is the room rent limit per day?", "product_code": "HLT-SHIELD", "version": "2025.1"})
check("policy assistant", q["grounded"] and q["citations"][0]["clause_ref"] == "2.2", q["answer"][:90])
refusal = call("POST", "/rag/query", {"question": "What is the capital of France?"})
check("assistant refuses without evidence", refusal["grounded"] is False)
print(f"All smoke checks passed against {BASE}")
