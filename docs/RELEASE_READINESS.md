# Release readiness — Claim Sense MVP

Status on 2026-10-09: **ready to deploy, not yet deployed.** The application works end to end locally in Docker on PostgreSQL. It also builds from a fresh clone. Deployment is blocked only because this build environment has no cloud account. Nothing here claims a deployment that has not been opened and smoke-tested.

## Blueprint MVP checklist (section 19)

| Item | State | Evidence |
|---|---|---|
| Repository audited and safe to modify | Done | `IMPLEMENTATION_STATUS.md` (starting point) |
| Eight core documents | Done | `PRD.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `DATABASE.md`, `SECURITY.md`, `CODE_STYLE.md`, `TESTING.md`, `AGENTS.md` |
| Frontend runs; backend runs | Done | Docker image serves both; smoke test `frontend`, `health`, `ready` |
| PostgreSQL schema works | Done | Docker stack on `postgres:16-alpine`; `/ready` reports `postgresql` |
| Policy PDF ingestion; clauses and pages preserved | Done | `test_policy_ingestion.py`; screenshot `15-policy-pdf-ingestion.png` |
| RAG retrieval; citations and evidence | Done | Evaluation: retrieval 39/39, citations 39/39, groundedness 69/69 |
| Claim creation, upload, extraction | Done | Smoke test; `test_extraction.py` |
| Policy version selection | Done | Evaluation C08, C11, C12 (both sides of 2025-04-01) |
| Coverage and exclusions; deterministic adjudication | Done | Evaluation: coverage 21/21, amounts 37/37 |
| Risk and fraud signals | Done | Evaluation: risk 15/15; portfolio precision 84.1%, recall 82.8% on injected anomalies |
| Human review; workflow transitions; audit | Done | `test_auth.py`, `test_golden_path.py`; browser approve and escalate |
| Dashboard | Done | Screenshot `14-dashboard-after-review.png` |
| Error states | Done | Uniform error body with correlation ID; `ErrorBox` on every screen; safe-failure test |
| Security controls reviewed; injection protections tested | Done | `SECURITY.md`; `test_security_guards.py`; evaluation Q21 |
| Tests pass | Done | 71 pytest, 256/256 evaluation checks, CI green on PR #1; PR #2 CI runs every push |
| Docker build works; README setup from a clean checkout | Done | Fresh clone of the branch built with `--no-cache` and passed the smoke test (2026-10-09). Behind a TLS-inspecting proxy, the build needs `--secret id=ca,src=<ca.crt>` (see README). |
| Data provenance; every RAG chunk traceable | Done | `DATA_PROVENANCE.md`; `scripts/provenance.py --check` in CI; `test_provenance.py`; screenshot `17-data-provenance.png` |
| No secrets or confidential data tracked | Done | `.gitignore`, `.dockerignore`; synthetic data only; `AUTH_SECRET` and `DEMO_PASSWORD` set by the environment |
| Deployment and deployed smoke test | **Blocked** | No cloud account in this environment. Render Blueprint (`render.yaml`) and Azure workflow are ready. |

## To go live

1. Merge the open pull request into `main`.
2. On render.com, choose New → Blueprint, then pick `CLAIM-SENSE`. Render reads `render.yaml`, builds the Dockerfile, provisions PostgreSQL and generates `AUTH_SECRET`. Set `DEMO_PASSWORD` when prompted.
3. Open the service URL and run `python3 scripts/smoke_test.py https://<service>.onrender.com <DEMO_PASSWORD>`.
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
