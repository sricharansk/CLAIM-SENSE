# Results dashboard

Source of the Claim Sense results dashboard published at https://claude.ai/artifact/FPQnN7TjiwjiwbqW7BSpau (a claude.ai artifact of the *Dashboard* type, private to the owner's account until shared).

- `index.html`: the page body (styles, markup and script). It runs inside the Dashboard artifact type and reads its datasets with `dash.data("<name>")`, so it is not a standalone web page.
- `data/claims.json`: one row per claim on the live site, from the read-only snapshot taken by the **Verify deployment** workflow on 2026-10-30 19:28 UTC ([run 41115415499](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/41115415499)), after the six-line release was deployed. The snapshot holds 72 claims across six lines, ₹2,22,18,600 billed and ₹1,61,98,470 payable. `incident_date` and `risk_score` are not in the log table; they come from `claims_report.py --live` against a fresh local start of the same commit, whose totals and checked rows match the run's.
- `data/deductions.json`: rupees removed per adjudication rule across those claims; the amounts sum to billed minus payable.
- `data/evaluation.json`: golden evaluation checks per dimension (986/986), from `reports/evaluation.json`.
- `data/portfolio.json`: risk rules on the 10,000-claim synthetic portfolio (six lines).

To refresh, run the Verify deployment workflow, rebuild `claims.json` and `deductions.json` from the `live-claims` artifact, and check the totals against the log's summary line. Then upload the files to the artifact's datasets (`claims`, `deductions`) and update the snapshot time in `index.html`. The steps are in `CLAUDE.md` under *Results dashboard*. All data is synthetic.
