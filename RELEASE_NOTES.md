# Release notes

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
