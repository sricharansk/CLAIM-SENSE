# Release notes

## Claim Sense 1.5.0 — 2026-10-30

- **Personal accident and life lines.** PA-SECURE and LIFE-TERM 2025.1 synthetic wordings with structured terms that cite their clauses. Benefits are paid from a schedule (share of the sum insured, the disablement table, a weekly benefit capped at ₹10,000, medical expenses up to 10%), in `Decimal`, with a clause on every step. Accident-only cover, the 12-month suicide exclusion and the life contestable period (section 45) are checked and cited.
- **72 seeded claims** (63 scenarios and 9 evaluation packets; 73 in the results report with the demo upload): 13 new seeded claims and 2 new evaluation packets, each with a hand-worked golden case. Golden evaluation: 986 / 986 checks over 72 claim cases and 30 questions. 158 backend tests.
- **10,000-claim synthetic portfolio** across all six lines: the risk rules find injected anomalies with 90.1% precision and 78.3% recall.
- **CAS Schedule P industry benchmark** on the Data sources screen and at `GET /api/v1/benchmarks/industry`: loss ratios and paid development for six US lines, aggregates only, downloaded and checked by `scripts/fetch_public_data.py`. It is context, not an input to any decision.
- **Blueprint documents**: `docs/API.md`, `ENVIRONMENT.md`, `ERROR_HANDLING.md`, `OBSERVABILITY.md`, `UX_FLOWS.md`, `ROADMAP.md` and `CHANGELOG.md`; decisions D27–D31.
- Rules and risk versions are now `adjudication-rules/1.1.0` and `risk-rules/1.1.0`. The smoke test and the browser tests file a personal accident and a life claim too.

## Claim Sense 1.4.3 — 2026-10-30

- **Windows and VS Code setup guide** (`docs/LOCAL_SETUP.md`) and VS Code tasks (`.vscode/`) to start the API and UI and run the tests.
- **Full validation re-run**: 127 backend tests, 803/803 golden checks, Docker + PostgreSQL smoke test, 12/12 browser tests; live site re-verified on 30 Oct 2026 with unchanged figures (57 claims, ₹86.96 L billed, ₹53.41 L payable).
- **Results dashboard** republished in the current claude.ai account with the 30 Oct snapshot.
- **Security:** pypdf 6.19.0 → 6.21.2, which fixes 11 advisories that `pip-audit` reported against 6.19.0.

## Claim Sense 1.4.2 — 2026-10-15

- **Project handover in `CLAUDE.md`**: a step-by-step guide to continuing on your own laptop (install, clone, pull, push, deploy), status, every pull request, how to run, deploy, verify and refresh the dashboard, and the open items, so work can continue on any machine.
- **Dashboard source and data** in `docs/dashboard/`; **presentation build script and inputs** in `docs/presentation/build/`.
- **Presentation updated** with the final status: project complete, live site re-verified on 15 Oct 2026, the live snapshot (57 seeded claims, ₹86.96 L billed, ₹53.41 L payable) beside the repository figures, the live-claims snapshot in the verify workflow, and the free hosting tier's restart limitation.

## Claim Sense 1.4.1 — 2026-10-13

- **Project complete.** The live deployment at https://claim-sense.onrender.com passes every check (57 seeded claims, 803/803 golden checks) after each restart of the free instance.
- **Review III presentation** in `docs/presentation/`, linked from the README.

## Claim Sense 1.4.0 — 2026-10-12

- **16 more seeded claims (50 in all; 57 in the live app, 58 in the results report).** Until now most seeded claims tested an exclusion; these cover the common payable situations on every line, each with a hand-worked golden case: hernia after the 24-month wait, ICU above the per-day limit, an accident inside the 30-day wait, a declared pre-existing disease after 36 months (health); a car over five years old, flood, a new car above 1500cc, malicious damage with a police report (motor); a burst pipe, a cyclone with underinsurance, an earthquake (property); a trip cut short by a family death, a large heart-attack claim, lost baggage inside every limit, an accident with an ambulance (travel).
- **A lapsed policy is now tested** (CLM-H-1021). The rejection for a loss outside the policy period now cites the coverage clause, as the passing check already did, so the letter quotes it.
- Golden evaluation: 803/803 checks over 57 claim cases and 26 questions. 127 backend tests.
- **Live claims report.** `scripts/claims_report.py --live URL` reports the claims on a deployed site, read-only, including reviewer decisions and claims filed there; the Verify deployment workflow saves it as the `live-claims` artifact before the smoke test runs.

## Claim Sense 1.3.1 — 2026-10-12

- **The live app holds every claim packet.** It used to start with the 34 seeded scenarios only, so the dashboard read 34 (37 after the smoke test) while the results report covered 42. The 7 evaluation packets are now seeded too, as CLM-H-1013 to 1016, CLM-P-3008 and CLM-T-4009/4010, each with its hand-worked outcome (`test_seed_packets.py`). A fresh start shows 41 claims; filing the demo upload makes 42.
- Interactive dashboard: every tile, line of business and bar opens the claims list with that filter. Pages are sent with `Cache-Control: no-cache` so a browser no longer keeps a stale unstyled page.
- The evaluation scorecard no longer clips three-digit counts; README screenshots regenerated by `e2e/screenshots.mjs`.

## Claim Sense 1.3.0 — 2026-10-12

- **Every rule in the four wordings is now exercised by a claim.** An audit found two rules that were written down but not applied: the health pre-existing disease waiting period (§3.2) and the motor police report for theft or malicious damage (§4.1). Both are now enforced.
- **15 more seeded claims (34 in all)**, one per rule that had none: cosmetic, alcohol, experimental treatment, the 30-day wait and pre-existing disease (health); mechanical breakdown, outside India, the higher deductible above 1500cc and malicious damage without a police report (motor); wilful act, act of war and a loss above the sum insured (property); alcohol, travel against medical advice and a medical claim without the doctor's report (travel).
- Golden evaluation: 612/612 checks over 41 claim cases and 26 questions. 108 backend tests.

## Claim Sense 1.2.0 — 2026-10-12

- **Live on Render** at https://claim-sense.onrender.com, verified by the **Verify deployment** workflow: every smoke check passed, including a health, a property and a travel claim ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)).
- **Four more seeded claims** for clauses no claim exercised: maternity (health §4.4), expired driving licence (motor §3.2), unoccupied home (property §3.3), pre-existing condition (travel §3.1). Golden evaluation: 449/449 checks over 26 claim cases and 26 questions.
- **Synthetic portfolio covers all four lines** (507 health, 241 motor, 124 property, 128 travel). Travel claims are scored without the early-claim signal, as in the live risk agent. Risk rules: precision 86.6%, recall 84.1% on injected anomalies.
- **No more Node.js 20 warnings in GitHub Actions:** checkout v5, setup-node v5, setup-python v6, upload-artifact v6 (all run on Node 24).

## Claim Sense 1.1.0 — 2026-10-12

- **Property and travel lines.** HOME-GUARD (householder) and TRV-GLOBE (overseas travel) wordings, each with clause-cited terms. New deterministic rules: depreciation on home contents, the average clause for underinsured homes (2.3), excess, per-item and per-trip baggage limits, trip-cancellation limit, non-payable personal comfort items, and the travel trip-period check (1.3). Documents required only for some losses (police report for burglary, airline irregularity report for lost baggage, medical report for treatment abroad) are checked from the claim text.
- **Seven new seeded claims and three new evaluation packets**, with hand-worked expectations. Golden evaluation: 405/405 checks over 22 claim cases and 26 questions.
- **Results on every claim.** `scripts/claims_report.py` runs all 23 claim packets through the API and writes `reports/claims_results.{json,md}`.
- New Claim screen offers all four lines; the smoke test and browser suite file a property and a travel claim.

## Claim Sense 1.0.0 (MVP) — 2026-10-09

**Claim Sense: RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant.** AI recommends, deterministic rules calculate, and people decide. All data is synthetic.

### What you can do

- **File a claim.** Create it, upload documents (PDF or text) and get extracted facts with file, line and confidence. Correct a misread fact with a reason before running the analysis.
- **Analyse it.** The analysis matches the policy version in force on the incident date. It retrieves the relevant clauses (hybrid BM25 and character n-grams) and checks coverage and exclusions. It calculates the payable amount with a Decimal waterfall that cites a clause at every step, scores risk with transparent signals, and recommends with an evidence package.
- **Review it.** The review queue shows priority, risk, age and assignee. Adjusters take tasks within a ₹2,00,000 approval limit; supervisors reassign and decide escalations. Adverse actions require notes.
- **Finish it.**
  - Generate settlement, repudiation, document-request and under-review letters from templates (never by an LLM).
  - Track the settlement deadline.
  - Export the claim register as CSV.
- **Ask about policies.** Answers come with citations; questions without evidence are refused.
- **Manage wordings.** Ingest a wording as PDF or Markdown, with checksum, page-preserving extraction and visible processing states.
- **Audit.** Every stage, from claim creation to final decision, is an audit event with a correlation ID.
- **Measure.** The dashboard shows claims, pending review, high risk, processing time, outcomes, override rate and escalation rate. The Evaluation screen shows the golden scorecard (405/405 in 1.1.0). The Data sources screen shows a verified source registry and a RAG manifest that traces every chunk to its source.
- **Use it on a phone.** The navigation collapses into a menu.

### Quality gates in CI

Every push runs:

- `ruff` and 71 `pytest` tests;
- the golden evaluation (fails on any miss) and the provenance check (registry, checksums, reproducible manifest);
- `pip-audit` and `npm audit`;
- a TypeScript build;
- a Docker + PostgreSQL stack with 10 Playwright browser tests and the smoke test.

### Run it

```bash
docker compose up --build -d          # http://localhost:8080, sign in as adjuster / supervisor / auditor
```

The password is `DEMO_PASSWORD`, which defaults to `claimsense-demo`. Deployment uses `render.yaml` (Render Blueprint) or the Azure Container Apps workflow; see `docs/DEPLOYMENT.md`.

### Known limitations

- Not yet deployed to a cloud: no cloud account was available while building.
- The LLM is off unless `ANTHROPIC_API_KEY` is set, so answers quote the wording.
- The demo accounts share one password, and there is no SSO.
- There is no OCR for scanned documents; they are refused with a clear message.
- Public 2024–2026 datasets are registered but not ingested.

Full status: `docs/IMPLEMENTATION_STATUS.md`. Validation: `docs/FINAL_VALIDATION_REPORT.md`.
