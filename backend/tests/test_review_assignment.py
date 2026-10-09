"""Review queue: risk, age and assignee shown; taking, releasing and reassigning tasks is role-checked and audited."""
from decimal import Decimal

from app.auth import hash_password
from app.db import SessionLocal
from app.models import User

from .conftest import login, new_claim


def _task(client, claim_number):
    return {t["claim_number"]: t for t in client.get("/api/v1/reviews").json()}[claim_number]


def _second_adjuster():
    with SessionLocal() as db:
        if not db.query(User).filter_by(username="adjuster2").first():
            db.add(User(username="adjuster2", display_name="Adjuster B. Iyer", role="ADJUSTER",
                        approval_limit=Decimal("200000"), password_hash=hash_password("claimsense-demo")))
            db.commit()


def test_queue_shows_risk_age_and_assignee(client):
    n = new_claim(client, "CLM-H-1003", "CS-HLT-25-000518", "health", "Arjun Mehta")
    t = _task(client, n)
    assert t["risk_level"] == "HIGH" and t["status"] == "PENDING_REVIEW"
    assert t["assignee"] is None and 0 <= t["age_hours"] < 1


def test_take_release_and_reassign(client):
    _second_adjuster()
    adj, adj2 = login(client, "adjuster"), login(client, "adjuster2")
    n = new_claim(client, "CLM-M-2001", "CS-MTR-25-001204", "motor", "Priya Sharma")
    task_id = _task(client, n)["task_id"]

    r = client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj, json={"username": "adjuster"})
    assert r.status_code == 200 and r.json()["assignee"] == "Adjuster A. Rao"
    assert _task(client, n)["assignee"] == "Adjuster A. Rao"

    # another adjuster can neither take it nor decide it
    r = client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj2, json={"username": "adjuster2"})
    assert r.status_code == 409 and "supervisor can reassign" in r.json()["error"]["message"]
    r = client.post(f"/api/v1/claims/{n}/review", headers=adj2, json={"action": "APPROVE"})
    assert r.status_code == 409
    # adjusters cannot hand work to someone else
    r = client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj, json={"username": "adjuster2"})
    assert r.status_code == 403

    # a supervisor reassigns; the new assignee decides
    r = client.post(f"/api/v1/reviews/{task_id}/assign", json={"username": "adjuster2"})
    assert r.json()["assignee"] == "Adjuster B. Iyer"
    r = client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj2, json={"username": None})
    assert r.status_code == 200 and r.json()["assignee"] is None
    assert client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj2, json={"username": "adjuster2"}).status_code == 200
    assert client.post(f"/api/v1/claims/{n}/review", headers=adj2, json={"action": "APPROVE"}).status_code == 200

    # the task is closed now
    assert client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj2, json={"username": None}).status_code == 409
    events = [(e["event_type"], e["details"].get("to")) for e in client.get(f"/api/v1/claims/{n}").json()["audit"]
              if e["event_type"].startswith("TASK_")]
    assert events == [("TASK_ASSIGNED", "Adjuster A. Rao"), ("TASK_ASSIGNED", "Adjuster B. Iyer"),
                      ("TASK_RELEASED", None), ("TASK_ASSIGNED", "Adjuster B. Iyer")]


def test_assignment_roles(client):
    n = new_claim(client, "CLM-H-1003", "CS-HLT-25-000518", "health", "Arjun Mehta")
    task_id = _task(client, n)["task_id"]
    assert client.post(f"/api/v1/reviews/{task_id}/assign", headers=login(client, "auditor"),
                       json={"username": None}).status_code == 403
    r = client.post(f"/api/v1/reviews/{task_id}/assign", json={"username": "auditor"})
    assert r.status_code == 422
    adj = login(client, "adjuster")
    client.post(f"/api/v1/claims/{n}/review", headers=adj, json={"action": "ESCALATE", "notes": "Above my limit"})
    r = client.post(f"/api/v1/reviews/{task_id}/assign", headers=adj, json={"username": "adjuster"})
    assert r.status_code == 403 and "supervisor queue" in r.json()["error"]["message"]
    assert client.post("/api/v1/reviews/999999/assign", json={"username": None}).status_code == 404
    names = {u["username"] for u in client.get("/api/v1/reviewers").json()}
    assert {"adjuster", "supervisor"} <= names and "auditor" not in names
