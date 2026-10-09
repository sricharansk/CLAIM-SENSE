# Release notes

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
- **Measure.** The dashboard shows claims, pending review, high risk, processing time, outcomes, override rate and escalation rate. The Evaluation screen shows the golden scorecard (256/256). The Data sources screen shows a verified source registry and a RAG manifest that traces every chunk to its source.
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
