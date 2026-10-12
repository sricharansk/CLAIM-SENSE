# Release readiness — Claim Sense MVP

Status on 2026-10-12: **deployed and verified.** Render serves `main` at https://claim-sense.onrender.com, and the **Verify deployment** workflow passed every smoke check against it ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)). The application also works end to end locally in Docker on PostgreSQL and builds from a fresh clone.

## Blueprint MVP checklist (section 19)

| Item | State | Evidence |
|---|---|---|
| Repository audited and safe to modify | Done | `IMPLEMENTATION_STATUS.md` (starting point) |
| Eight core documents | Done | `PRD.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `DATABASE.md`, `SECURITY.md`, `CODE_STYLE.md`, `TESTING.md`, `AGENTS.md` |
| Frontend runs; backend runs | Done | Docker image serves both; smoke test `frontend`, `health`, `ready` |
| PostgreSQL schema works | Done | Docker stack on `postgres:16-alpine`; `/ready` reports `postgresql` |
| Policy PDF ingestion; clauses and pages preserved | Done | `test_policy_ingestion.py`; screenshot `15-policy-pdf-ingestion.png` |
| RAG retrieval; citations and evidence | Done | Evaluation: retrieval 91/91, citations 67/67, groundedness 113/113 |
| Claim creation, upload, extraction | Done | Smoke test; `test_extraction.py` |
| Policy version selection | Done | Evaluation C08, C11, C12 (both sides of 2025-04-01) |
| Coverage and exclusions; deterministic adjudication | Done | Evaluation: coverage 79/79, amounts 95/95 |
| Risk and fraud signals | Done | Evaluation: risk 44/44; portfolio (four lines) precision 86.6%, recall 84.1% on injected anomalies |
| Human review; workflow transitions; audit | Done | `test_auth.py`, `test_golden_path.py`; browser approve and escalate |
| Dashboard | Done | Screenshot `14-dashboard-after-review.png` |
| Error states | Done | Uniform error body with correlation ID; `ErrorBox` on every screen; safe-failure test |
| Security controls reviewed; injection protections tested | Done | `SECURITY.md`; `test_security_guards.py`; evaluation Q21 |
| Tests pass | Done | 126 pytest, 12 Playwright browser tests, 803/803 evaluation checks, provenance check; CI green on PR #1; PR #2 CI runs every push. Full report: `FINAL_VALIDATION_REPORT.md` |
| Docker build works; README setup from a clean checkout | Done | Fresh clone of the branch built with `--no-cache` and passed the smoke test (2026-10-09). Behind a TLS-inspecting proxy, the build needs `--secret id=ca,src=<ca.crt>` (see README). |
| Data provenance; every RAG chunk traceable | Done | `DATA_PROVENANCE.md`; `scripts/provenance.py --check` in CI; `test_provenance.py`; screenshot `17-data-provenance.png` |
| No secrets or confidential data tracked | Done | `.gitignore`, `.dockerignore`; synthetic data only; `AUTH_SECRET` and `DEMO_PASSWORD` set by the environment |
| Deployment and deployed smoke test | Done | Render Blueprint (`render.yaml`); smoke test passed against https://claim-sense.onrender.com on 2026-10-12 ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)) |

## To go live

1. Merge the open pull request into `main`.
2. On render.com, choose New → Blueprint, then pick `CLAIM-SENSE`. Render reads `render.yaml`, builds the Dockerfile, provisions PostgreSQL and generates `AUTH_SECRET`. Set `DEMO_PASSWORD` when prompted.
3. Open the service URL and run `python3 scripts/smoke_test.py https://<service>.onrender.com <DEMO_PASSWORD>`, or run the **Verify deployment** workflow with the URL.
4. Only after that passes, record the URL and result in `IMPLEMENTATION_STATUS.md`.

## Known limits (enterprise gates, not MVP defects)

- **Data and integration:**
  - Synthetic data only.
  - No insurer core-system integration.
  - No OCR for scanned documents (they are refused with a clear message).
- **Sign-in and roles:**
  - Demo accounts share one password; there is no SSO or user management.
  - The sign-in throttle is per app instance.
- **AI and retrieval:**
  - The LLM is off unless `ANTHROPIC_API_KEY` is set; answers are extractive quotes.
  - Retrieval uses an in-process index (BM25 + character n-grams), not a managed vector service.
- **Governance:** formal compliance, legal review and production data governance are outside this build.
