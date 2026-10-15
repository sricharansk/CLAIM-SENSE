# Results dashboard

Source of the Claim Sense results dashboard published at https://claude.ai/artifact/XzzbSf7X1PYcxwThkMvb1V (a claude.ai artifact of the *Dashboard* type, private to the owner's account until shared).

- `index.html`: the page body (styles, markup and script). It runs inside the Dashboard artifact type and reads its datasets with `dash.data("<name>")`, so it is not a standalone web page.
- `data/claims.json`: one row per claim on the live site, from the read-only snapshot taken by the **Verify deployment** workflow on 2026-10-15 05:11 UTC ([run 38685398836](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38685398836)). The snapshot holds 57 claims, ₹86,95,600 billed and ₹53,41,470 payable.
- `data/deductions.json`: rupees removed per adjudication rule across those claims; the amounts sum to billed minus payable.
- `data/evaluation.json`: golden evaluation checks per dimension (803/803), from `reports/evaluation.json`.
- `data/portfolio.json`: risk rules on the 1,000-claim synthetic portfolio.

To refresh, run the Verify deployment workflow, rebuild `claims.json` and `deductions.json` from the `live-claims` artifact, and check the totals against the log's summary line. Then upload the files to the artifact's datasets (`claims`, `deductions`) and update the snapshot time in `index.html`. The steps are in `CLAUDE.md` under *Results dashboard*. All data is synthetic.
