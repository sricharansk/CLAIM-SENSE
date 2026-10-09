"""Reviewer corrections of extracted facts: recorded, audited, used by the next analysis, extracted value kept."""
from .conftest import login, new_claim


def _view(client, n):
    return {f["name"]: f for f in client.get(f"/api/v1/claims/{n}").json()["fact_view"]}


def test_correction_is_used_by_next_analysis_and_audited(client):
    n = new_claim(client, "CLM-M-2001", "CS-MTR-25-001204", "motor", "Priya Sharma")
    before = _view(client, n)["incident_date"]
    assert not before["corrected"] and before["source"]["document"]
    r = client.post(f"/api/v1/claims/{n}/facts", headers=login(client, "adjuster"),
                    json={"name": "incident_date", "value": "2025-06-03", "reason": "Police report gives the 3rd"})
    assert r.status_code == 201 and r.json()["previous"] == before["value"]

    fact = _view(client, n)["incident_date"]
    assert fact["corrected"] and fact["value"] == "2025-06-03" and fact["extracted_value"] == before["value"]
    assert fact["source"]["document_type"] == "reviewer_correction" and "Police report" in fact["source"]["text"]

    a = client.post(f"/api/v1/claims/{n}/analyze").json()
    assert a["result"]["facts"]["incident_date"] == "2025-06-03"
    assert a["result"]["fact_sources"]["incident_date"]["document_type"] == "reviewer_correction"
    event = next(e for e in client.get(f"/api/v1/audit?claim_number={n}").json() if e["event_type"] == "FACT_CORRECTED")
    assert event["actor"] == "adjuster" and event["details"]["from"] == before["value"]
    assert event["details"]["to"] == "2025-06-03"

    # the latest correction wins
    client.post(f"/api/v1/claims/{n}/facts", json={"name": "incident_date", "value": "2025-06-04", "reason": "Supervisor check"})
    assert _view(client, n)["incident_date"]["value"] == "2025-06-04"


def test_correction_validation(client):
    n = new_claim(client, "CLM-H-1005", "CS-HLT-24-000233", "health", "Suresh Nair")
    post = lambda body, **kw: client.post(f"/api/v1/claims/{n}/facts", json=body, **kw)  # noqa: E731
    assert post({"name": "incident_date", "value": "03/06/2025", "reason": "x"}).status_code == 422
    assert post({"name": "claimed_amount", "value": "-5", "reason": "x"}).status_code == 422
    assert post({"name": "claimed_amount", "value": "abc", "reason": "x"}).status_code == 422
    assert post({"name": "document_total", "value": "1", "reason": "x"}).status_code == 422
    assert post({"name": "diagnosis", "value": "Cataract", "reason": " "}).status_code == 422
    assert post({"name": "diagnosis", "value": "Cataract", "reason": "x"}, headers=login(client, "auditor")).status_code == 403
    r = post({"name": "claimed_amount", "value": "76,500", "reason": "Typo on the form"})
    assert r.status_code == 201 and r.json()["value"] == "76500.00"
    client.post(f"/api/v1/claims/{n}/review", json={"action": "APPROVE"})
    assert post({"name": "diagnosis", "value": "Cataract", "reason": "late"}).status_code == 409
