from fastapi.testclient import TestClient

from app.main import app

from .conftest import login, new_claim


def test_api_requires_sign_in(client):
    anon = TestClient(app)
    assert anon.get("/api/v1/health").status_code == 200
    r = anon.get("/api/v1/claims")
    assert r.status_code == 401 and r.json()["error"]["message"] == "Sign in to continue"
    assert anon.get("/api/v1/claims", headers={"Authorization": "Bearer forged.token"}).status_code == 401


def test_wrong_password_rejected(client):
    r = client.post("/api/v1/auth/login", json={"username": "adjuster", "password": "nope"})
    assert r.status_code == 401


def test_me_returns_role(client):
    me = client.get("/api/v1/auth/me", headers=login(client, "adjuster")).json()
    assert me["role"] == "ADJUSTER" and me["approval_limit"] == "200000.00" and me["can_write"]


def test_auditor_is_read_only(client):
    h = login(client, "auditor")
    assert client.get("/api/v1/claims", headers=h).status_code == 200
    r = client.post("/api/v1/claims", headers=h, json={"policy_number": "CS-HLT-24-000117", "claim_type": "health",
                                                       "claimant_name": "Ravi Kumar"})
    assert r.status_code == 403


def test_adjuster_approval_limit_and_escalation(client):
    adj = login(client, "adjuster")
    n = new_claim(client, "CLM-H-1003", "CS-HLT-25-000518", "health", "Arjun Mehta")
    # the bill packet recommends 332,100.00, above the adjuster's 200,000 limit
    r = client.post(f"/api/v1/claims/{n}/review", headers=adj, json={"action": "APPROVE"})
    assert r.status_code == 403 and "approval limit" in r.json()["error"]["message"]
    r = client.post(f"/api/v1/claims/{n}/review", headers=adj, json={"action": "ESCALATE", "notes": "Above my limit"})
    assert r.json()["status"] == "ESCALATED"
    assert {t["claim_number"]: t for t in client.get("/api/v1/reviews").json()}[n]["queue"] == "SUPERVISOR_REVIEW"
    r = client.post(f"/api/v1/claims/{n}/review", headers=adj, json={"action": "REJECT", "notes": "x"})
    assert r.status_code == 403
    r = client.post(f"/api/v1/claims/{n}/review", json={"action": "INVESTIGATE", "notes": "Refer to SIU"})
    assert r.json()["status"] == "UNDER_INVESTIGATION"
    assert {t["claim_number"]: t for t in client.get("/api/v1/reviews").json()}[n]["queue"] == "SIU_INVESTIGATION"


def test_only_supervisor_ingests_policies(client):
    r = client.post("/api/v1/policies", headers=login(client, "adjuster"),
                    files={"wording": ("t.md", b"## 1. A\\n### 1.1 B\\ntext\\n"), "terms": ("t.json", b"{}")})
    assert r.status_code == 403


def test_decisions_record_signed_in_user(client):
    adj = login(client, "adjuster")
    n = new_claim(client, "CLM-M-2001", "CS-MTR-25-001204", "motor", "Priya Sharma")
    r = client.post(f"/api/v1/claims/{n}/review", headers=adj, json={"action": "APPROVE"})
    assert r.status_code == 200
    d = client.get(f"/api/v1/claims/{n}").json()["decisions"][-1]
    assert d["actor"] == "Adjuster A. Rao" and d["payable_amount"] == "55350.00"
