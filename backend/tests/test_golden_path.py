import json

import pytest

from .conftest import DATA

SCENARIOS = json.loads((DATA / "claims" / "scenarios.json").read_text())


@pytest.mark.parametrize("s", SCENARIOS, ids=[s["claim_number"] for s in SCENARIOS])
def test_seeded_scenarios_reach_expected_recommendation(client, s):
    c = client.get(f"/api/v1/claims/{s['claim_number']}").json()
    assert c["analysis"]["status"] == "SUCCEEDED"
    assert c["recommendation"] == s["expected_recommendation"], s["scenario"]
    assert c["status"] == "PENDING_REVIEW"
    assert [a["agent"] for a in c["analysis"]["agents"]][0] == "Intake Agent"


def test_version_matching_uses_wording_in_force(client):
    r = client.get("/api/v1/claims/CLM-H-1005/analysis").json()["result"]
    assert r["policy"]["version"] == "2024.1"
    r = client.get("/api/v1/claims/CLM-H-1001/analysis").json()["result"]
    assert r["policy"]["version"] == "2025.1"
    assert r["adjudication"]["payable_amount"] == "84330.00"


def test_rejection_cites_clause(client):
    r = client.get("/api/v1/claims/CLM-M-2002/analysis").json()["result"]
    fail = next(f for f in r["coverage"]["findings"] if f["outcome"] == "FAIL")
    assert fail["code"] == "EXCL_DUI" and fail["citation"]["clause_ref"] == "3.1"
    assert r["adjudication"]["payable_amount"] == "0.00"


def test_duplicate_detected(client):
    r = client.get("/api/v1/claims/CLM-H-1006/analysis").json()["result"]
    assert "POSSIBLE_DUPLICATE" in {s["code"] for s in r["risk"]["signals"]}


def _upload(client, number, folder, names):
    files = [("files", (n, (DATA / "claims" / folder / n).read_bytes(), "text/plain")) for n in names]
    return client.post(f"/api/v1/claims/{number}/documents", files=files)


def test_end_to_end_create_upload_analyse_review(client):
    c = client.post("/api/v1/claims", json={"policy_number": "CS-HLT-23-000089", "claim_type": "health",
                                             "claimant_name": "Fatima Shaikh", "description": "kidney stone"})
    assert c.status_code == 201
    n = c.json()["claim_number"]
    assert client.post(f"/api/v1/claims/{n}/review", json={"action": "APPROVE", "reviewer": "qa"}).status_code == 409
    up = _upload(client, n, "demo_upload", ["claim_form.txt", "hospital_bill.txt", "discharge_summary.txt"])
    assert up.status_code == 201 and {d["doc_type"] for d in up.json()} == {"claim_form", "hospital_bill", "discharge_summary"}
    a = client.post(f"/api/v1/claims/{n}/analyze").json()
    assert a["status"] == "SUCCEEDED"
    assert a["result"]["recommendation"]["decision"] == "PARTIAL_APPROVAL"
    assert a["result"]["adjudication"]["payable_amount"] == "64080.00"
    # re-run is safe: still exactly one open workflow task
    client.post(f"/api/v1/claims/{n}/analyze")
    assert sum(1 for t in client.get("/api/v1/reviews").json() if t["claim_number"] == n) == 1
    bad = client.post(f"/api/v1/claims/{n}/review", json={"action": "REJECT", "reviewer": "qa", "notes": ""})
    assert bad.status_code == 422 and "correlation_id" in bad.json()["error"]
    ok = client.post(f"/api/v1/claims/{n}/review", json={"action": "APPROVE", "reviewer": "qa", "payable_amount": "60000"})
    assert ok.json() == {"claim_number": n, "status": "APPROVED", "decision": "APPROVE", "payable_amount": "60000.00"}
    events = [e["event_type"] for e in client.get(f"/api/v1/audit?claim_number={n}").json()]
    assert {"CLAIM_CREATED", "DOCUMENT_UPLOADED", "ANALYSIS_STARTED", "FACTS_EXTRACTED", "POLICY_SELECTED",
            "EVIDENCE_RETRIEVED", "COVERAGE_ANALYZED", "ADJUDICATION_CALCULATED", "RISK_SCORED", "EVIDENCE_PACKAGED",
            "AI_RECOMMENDATION", "HUMAN_DECISION"} <= set(events)
    trail = {e["event_type"]: e for e in client.get(f"/api/v1/audit?claim_number={n}").json()}
    assert trail["ADJUDICATION_CALCULATED"]["details"]["payable_amount"] == "64080.00"
    assert trail["POLICY_SELECTED"]["details"]["version"] == trail["AI_RECOMMENDATION"]["details"]["policy_version"]
    assert trail["HUMAN_DECISION"]["details"]["override"] is True and trail["HUMAN_DECISION"]["details"]["final"] is True
    assert client.post(f"/api/v1/claims/{n}/analyze").status_code == 409


def test_analysis_fails_safely_without_incident_date(client):
    n = client.post("/api/v1/claims", json={"policy_number": "CS-HLT-24-000117", "claim_type": "health",
                                             "claimant_name": "Ravi Kumar"}).json()["claim_number"]
    files = [("files", ("note.txt", b"Patient Name: Ravi Kumar\nSome note without dates\n", "text/plain"))]
    assert client.post(f"/api/v1/claims/{n}/documents", files=files).status_code == 201
    a = client.post(f"/api/v1/claims/{n}/analyze").json()
    assert a["status"] == "FAILED" and "Incident date" in a["error"]
    assert client.get(f"/api/v1/claims/{n}").json()["status"] == "NEEDS_ATTENTION"


def test_upload_validation(client):
    n = client.post("/api/v1/claims", json={"policy_number": "CS-HLT-24-000117", "claim_type": "health",
                                             "claimant_name": "Ravi Kumar"}).json()["claim_number"]
    r = client.post(f"/api/v1/claims/{n}/documents", files=[("files", ("x.exe", b"MZ", "application/octet-stream"))])
    assert r.status_code == 422
    assert client.post("/api/v1/claims", json={"policy_number": "NOPE-1", "claim_type": "health",
                                                "claimant_name": "X Y"}).status_code == 422


def test_policy_ingestion_rejects_unknown_clause_refs(client):
    md = "## 1. Cover\n### 1.1 Cover\nEverything is covered.\n"
    terms = {"product_code": "TST", "product_name": "T", "line_of_business": "health", "version": "1",
             "effective_from": "2025-01-01", "effective_to": "2025-12-31", "deductible": {"amount": 1, "clause": "9.9"},
             "required_documents": {"documents": [], "clause": "1.1"}}
    r = client.post("/api/v1/policies", files={"wording": ("t.md", md.encode()), "terms": ("t.json", json.dumps(terms).encode())})
    assert r.status_code == 422 and "9.9" in r.json()["error"]["message"]


def test_health_ready_and_analytics(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/ready").json()["policy_index"] == "ok"
    a = client.get("/api/v1/analytics").json()
    assert a["totals"]["claims"] >= 8
    assert a["portfolio"]["claims"] == 1000 and 0 < a["portfolio"]["recall"] <= 1


def test_security_headers_and_error_shape(client):
    r = client.get("/api/v1/claims/DOES-NOT-EXIST")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "HTTP_404" and r.json()["error"]["correlation_id"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_upload_filename_cannot_escape_storage(client):
    n = client.post("/api/v1/claims", json={"policy_number": "CS-HLT-24-000117", "claim_type": "health",
                                             "claimant_name": "Ravi Kumar"}).json()["claim_number"]
    files = [("files", ("../../../etc/evil.txt", b"Policy Number: CS-HLT-24-000117\n", "text/plain"))]
    r = client.post(f"/api/v1/claims/{n}/documents", files=files)
    assert r.status_code == 201 and r.json()[0]["filename"] == "evil.txt"


def test_api_docs_page_loads(client):
    r = client.get("/docs")
    assert r.status_code == 200 and "content-security-policy" not in r.headers
