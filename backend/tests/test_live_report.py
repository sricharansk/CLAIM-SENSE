import importlib.util

from app.config import REPO_ROOT

_spec = importlib.util.spec_from_file_location("claims_report", REPO_ROOT / "scripts" / "claims_report.py")
claims_report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims_report)


def test_live_snapshot_reports_every_claim_without_changing_any(client):
    """`claims_report.py --live` reads a deployed site; the same code runs here against the test API."""
    before = client.get("/api/v1/claims").json()
    report = claims_report.build_live(client)
    assert client.get("/api/v1/claims").json() == before  # read-only
    rows = {r["claim_number"]: r for r in report["claims"]}
    # claims created without an analysis yet are listed apart, not counted
    assert set(rows) | set(report["not_analysed"]) == {c["claim_number"] for c in before}
    assert not set(rows) & set(report["not_analysed"])
    assert rows["CLM-H-1001"]["source"] == "seeded scenario" and rows["CLM-H-1001"]["payable"] == "84330.00"
    assert all(r["queue"] for r in rows.values())  # every claim is in a review queue or decided by a person
    assert report["summary"]["claims"] == len(rows)
    assert "Snapshot of" not in claims_report.to_markdown(report)  # source_url is set only by main_live
