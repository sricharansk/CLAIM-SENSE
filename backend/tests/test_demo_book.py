"""The seeded demo book: designed outcomes, replayed review history, dashboard filters and drill-downs."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.agents.review import ACTIONS
from app.seed import HISTORY_NOTE

from .conftest import DATA

BOOK = json.loads((DATA / "claims" / "demo_book.json").read_text())


def _utc(s: str) -> datetime:
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@pytest.mark.parametrize("s", BOOK, ids=[s["claim_number"] for s in BOOK])
def test_demo_claim_reaches_its_designed_outcome(client, s):
    c = client.get(f"/api/v1/claims/{s['claim_number']}").json()
    assert c["recommendation"] == s["expected_recommendation"], s["scenario"]


def test_book_covers_both_lines_and_every_outcome():
    assert {s["claim_type"] for s in BOOK} == {"health", "motor"}
    assert {s["expected_recommendation"] for s in BOOK} == {"PARTIAL_APPROVAL", "RECOMMEND_REJECT", "REQUEST_INFO", "INVESTIGATE"}
    assert len({s["policy_number"] for s in BOOK}) >= 40


@pytest.mark.parametrize("s", [s for s in BOOK if s["history"]], ids=[s["claim_number"] for s in BOOK if s["history"]])
def test_history_is_replayed_through_the_review_path_and_labelled(client, s):
    c = client.get(f"/api/v1/claims/{s['claim_number']}").json()
    assert c["status"] == ACTIONS[s["history"][-1]["action"]]
    human = [d for d in c["decisions"] if d["source"] == "HUMAN"]
    assert [d["decision"] for d in human] == [h["action"] for h in s["history"]]
    assert all(d["notes"].startswith(HISTORY_NOTE) for d in human)
    filed = _utc(c["created_at"])
    assert abs((datetime.now(timezone.utc) - filed) - timedelta(days=s["age_days"])) < timedelta(hours=1)
    for d, h in zip(human, s["history"], strict=True):
        assert _utc(d["created_at"]) - filed == timedelta(days=h["after_days"], hours=3)
    events = [e for e in c["audit"] if e["event_type"] == "HUMAN_DECISION"]
    assert len(events) == len(human) and all(_utc(e["created_at"]) > filed for e in events)


def test_replayed_decisions_follow_the_review_rules(client):
    names = {r["username"]: r["display_name"] for r in client.get("/api/v1/reviewers").json()}
    for s in BOOK:
        c = client.get(f"/api/v1/claims/{s['claim_number']}").json()
        human = [d for d in c["decisions"] if d["source"] == "HUMAN"]
        for d, h in zip(human, s["history"], strict=True):
            assert d["actor"] == names[h["actor"]]
            if d["decision"] in ("REJECT", "ESCALATE", "INVESTIGATE"):
                assert d["notes"].strip() != HISTORY_NOTE.strip(), s["claim_number"]
            if d["decision"] == "APPROVE" and h["actor"] == "adjuster":
                assert float(d["payable_amount"]) <= 200000, s["claim_number"]


def test_dashboard_filters_and_panels(client):
    whole = client.get("/api/v1/analytics").json()
    motor = client.get("/api/v1/analytics?line=motor").json()
    week = client.get("/api/v1/analytics?days=7").json()
    assert motor["filters"] == {"line": "motor", "days": None}
    assert motor["totals"]["claims"] == whole["by_line"]["motor"] < whole["totals"]["claims"]
    assert 0 < week["totals"]["claims"] < whole["totals"]["claims"]
    assert len(whole["trend"]) == 8 and sum(w["filed"] for w in whole["trend"]) <= whole["totals"]["claims"]
    assert sum(w["decided"] for w in whole["trend"]) > 0
    open_claims = sum(n for s, n in whole["by_status"].items() if s not in ("APPROVED", "REJECTED"))
    assert sum(whole["ageing"].values()) == open_claims and whole["ageing"]["Over 30 days"] >= 1
    assert any("overdue" in r for row in whole["attention"] for r in row["reasons"])
    codes = {r["code"]: r["clause_ref"] for r in whole["top_reasons"]}
    assert codes["SPECIFIED_DISEASE_WAITING"] == "3.3" and "REQUIRED_DOCUMENTS" in codes
    assert whole["human_vs_ai"]["overridden"] >= 1 and whole["human_vs_ai"]["escalated"] >= 2
    assert whole["totals"]["avg_days_to_decision"] > 0
    assert client.get("/api/v1/analytics?line=travel").status_code == 422


def test_claims_list_drill_down_filters(client):
    get = lambda qs: client.get(f"/api/v1/claims?{qs}").json()  # noqa: E731
    assert {c["risk_level"] for c in get("risk=HIGH")} == {"HIGH"}
    assert {c["claim_type"] for c in get("claim_type=motor")} == {"motor"}
    assert {c["recommendation"] for c in get("recommendation=REQUEST_INFO")} == {"REQUEST_INFO"}
    overdue = get("settlement=OVERDUE")
    assert overdue and {c["settlement"]["state"] for c in overdue} == {"OVERDUE"}
    assert {c["status"] for c in get("status=APPROVED,REJECTED")} == {"APPROVED", "REJECTED"}
    recent = get("days=7")
    assert recent and len(recent) < len(get("")) and all(
        datetime.now(timezone.utc) - _utc(c["created_at"]) <= timedelta(days=7) for c in recent)
    assert client.get("/api/v1/auth/demo-info").json() == {"default_password": True}


def test_sample_packet_is_served_for_the_new_claim_screen(client):
    p = client.get("/api/v1/demo-packet").json()
    assert p["policy_number"] == "CS-HLT-23-000089" and p["claim_type"] == "health" and "kidney stone" in p["description"]
    assert [f["name"] for f in p["files"]] == ["claim_form.txt", "discharge_summary.txt", "hospital_bill.txt"]
    assert "Itemised Charges" in client.get("/api/v1/demo-packet/hospital_bill.txt").text
    assert client.get("/api/v1/demo-packet/secrets.txt").status_code == 404
