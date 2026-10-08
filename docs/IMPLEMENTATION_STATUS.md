# Implementation Status

Last updated: 2026-10-08. Source of truth: `docs/Claim_Sense_Project_1_..._FINAL_V2_..._Deployment_Ready.md` and `PROJECT_1_FINAL_CONTENTS.md`.

## Starting point

The repository held one file, `PROJECT 1.MD` (the original project prompt). There was no code, build, test, Docker or deployment configuration. Everything below was built in this pass.

## Completed (validated)

| # | Golden-path step | Implementation | Validation |
|---|---|---|---|
| 1 | Dashboard | `frontend/src/pages/Dashboard.tsx`, `GET /api/v1/analytics` | Browser run, screenshot `docs/screenshots/01-dashboard.png` |
| 2 | Claim creation and document upload | `POST /claims`, `POST /claims/{n}/documents`, `NewClaim.tsx` | Browser upload of `data/claims/demo_upload`, API test |
| 3 | Extraction and structured facts | `agents/document.py` (PDF via pypdf, text), facts with file/line/confidence | `test_extraction.py` incl. PDF |
| 4 | Policy and version matching | `agents/policy.py`, effective-dated `policy_versions` | `test_version_matching_uses_wording_in_force` |
| 5 | Hybrid RAG | `rag/retriever.py` BM25 + char n-gram TF-IDF, RRF, synonym expansion | `test_rag.py` |
| 6 | Evidence with source metadata | clause ref, section, page, version, file on every citation | `test_rejection_cites_clause`, smoke test |
| 7 | Coverage and exclusions | `agents/coverage.py` | 8 golden scenarios |
| 8 | Deterministic adjudication | `adjudication/rules.py` (Decimal, waterfall) | `test_adjudication.py` hand calculations |
| 9 | Fraud/risk signals | `agents/risk.py` | `test_risk_levels`, duplicate test, portfolio evaluation |
| 10 | Evidence-backed recommendation | `agents/evidence.py` | 8 golden scenarios |
| 11 | Human review and workflow | `agents/review.py`, `/review`, `/reviews` | API test incl. validation and override audit; browser approve |
| 12 | Audit trail | `audit_events`, `/audit` | API test, browser |
| 13 | Interactive frontend | 9 screens, all calling real endpoints | Playwright golden path: 0 console errors |
| – | Supervisor/orchestrator | `agents/supervisor.py`, `analysis_runs`, `agent_runs` with tool calls | Safe-failure and re-run tests |
| – | Docker | `Dockerfile` (UI + API in one image), `docker-compose.yml` with PostgreSQL | Built and run locally on PostgreSQL; smoke test passed |
| – | CI | `.github/workflows/ci.yml`: ruff, pytest, pip-audit, npm audit, frontend build, Docker + PostgreSQL smoke test | First run on PR #1: all jobs passed |
| – | Sign-in and roles | `auth.py`, `/auth/login`, `/auth/me`; adjuster / supervisor / auditor; approval limit and escalation rules; sign-in screen and role-aware UI | `test_auth.py` (7 tests); browser run signs in and sees approval blocked over the limit |
| – | Security | Upload allow-list, size limit and filename sanitising; security headers and CSP; non-root container; dependency audits; see `docs/SECURITY.md` | Header and path tests; pip-audit and npm audit clean |

## Validation results (this session)

- `ruff check app tests`: clean.
- `pytest`: 42 passed.
- `npm run build` (tsc + vite): passed.
- `pip-audit -r backend/requirements.txt`: no known vulnerabilities. `npm audit`: 0 vulnerabilities.
- GitHub Actions CI run 1 on PR #1: backend, frontend and docker-smoke jobs passed.
- Browser (Playwright, Chromium) against Vite dev server and against the Docker image on PostgreSQL: create claim, upload 3 documents, analyse (₹78,000 billed, ₹64,080 payable, partial approval), approve, assistant answer and refusal, all pages load. No console errors on the Docker run.
- `scripts/smoke_test.py http://localhost:8080` against Docker + PostgreSQL: all checks passed.

## Definition of done (blueprint PART 20)

| Item | State |
|---|---|
| Repository audited; source-of-truth docs created | Done |
| Backend runs; frontend runs; database migrates; demo data loads | Done (SQLite and PostgreSQL) |
| Policy ingests; claim ingests; document extraction | Done |
| Policy/version matching; hybrid RAG; citations resolve | Done |
| Coverage; deterministic adjudication; risk/fraud; supervisor | Done |
| Human review; audit; dashboard | Done |
| Golden tests pass; security checks pass; Docker works; repository clean | Done |
| Deployment succeeds; deployed health check; deployed smoke test | **Blocked**: needs a cloud account (see below) |

## In progress

Nothing in progress.

## Blocked

| Item | Blocker | What unblocks it |
|---|---|---|
| Cloud deployment (Azure Container Apps or Render) | No cloud credentials or account access in the build environment | Add `AZURE_CREDENTIALS` secret and variables, then run the *Deploy to Azure Container Apps* workflow; or connect the repo on Render using `render.yaml` |
| LLM-written answers | No `ANTHROPIC_API_KEY` provided | Set the key; extractive mode works without it |
| Public 2024–2026 datasets | Registered only; not downloaded or ingested | Download, record provenance, ingest IRDAI circulars into the RAG corpus |

## Not in this version (roadmap)

Single sign-on and user management, OCR for scanned images, embedding retriever, ML fraud model, property and travel lines, background job queue, Azure AI Search, Key Vault, Application Insights, reopening decided claims.

## Next action

Merge PR #1 (Render deploys from the default branch), then deploy with one of the two prepared paths and run `python3 scripts/smoke_test.py <deployed-url>`. Deployment is not claimed until that passes.
