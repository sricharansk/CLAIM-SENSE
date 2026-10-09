# Final validation report — Claim Sense MVP

Blueprint Prompt 20. Branch `claude/project-thread-lu5h1l` (pull request #2), checked on 2026-10-09.

**Bottom line:** the MVP works end to end on Docker with PostgreSQL. Every check below was run. Cloud deployment is the one blocked item: this build environment has no cloud account. A deployed URL has not been opened or smoke-tested, so deployment is not claimed.

Classification:

- **VERIFIED:** the test or user-visible check was executed and passed.
- **BLOCKED:** it cannot be run from here, for the reason given.
- **POST_MVP:** deliberately out of scope for this release.

## Golden path

Each step was driven through the real UI by `e2e/tests/golden.spec.mjs` (Playwright, Chromium) against the Docker image on a fresh PostgreSQL volume. Each step was also driven through the API by `scripts/smoke_test.py` and `backend/tests/test_golden_path.py`.

| Step | State | Evidence |
|---|---|---|
| Login | VERIFIED | Browser sign-in for adjuster, supervisor and auditor; smoke `sign in`, `API requires sign-in` (401) |
| Dashboard | VERIFIED | Browser: dashboard and review-rate KPIs; `test_security_guards.py` checks the rates |
| Create claim | VERIFIED | Browser *golden path*; smoke `create claim` |
| Upload documents | VERIFIED | Browser uploads the 3 demo documents; smoke `upload + extract` (6, 12 and 7 facts) |
| Extract facts | VERIFIED | `test_extraction.py` (text and PDF); fact correction and re-run in the browser; `test_fact_correction.py` |
| Policy/version match | VERIFIED | Evaluation C08, C11 and C12 (both sides of 2025-04-01); `test_version_matching_uses_wording_in_force` |
| RAG | VERIFIED | Evaluation: retrieval 39/39, hit@1 100%, MRR 1.00; RAG manifest has 54 chunks, 0 rejected |
| Evidence | VERIFIED | Evaluation: citations 39/39, groundedness 69/69; browser *Policy & evidence* tab; smoke `citations` (13 items) |
| Coverage | VERIFIED | Evaluation: coverage 21/21; browser rejection cites §3.3 |
| Adjudication | VERIFIED | Browser and smoke: ₹64,080 payable on ₹78,000 billed; evaluation amounts 37/37; `test_adjudication.py` (7 hand calculations) |
| Risk | VERIFIED | Evaluation: risk 15/15; `test_security_guards.py` (planted-instruction signal) |
| Recommendation | VERIFIED | Browser: *Partial approval*; evaluation: workflow 36/36 |
| Human review | VERIFIED | Browser: approve, approval-limit block, take and release a task; `test_auth.py`; `test_review_assignment.py` |
| Decision | VERIFIED | Browser: status *Approved* and a settlement letter for INR 64,080.00; smoke `human review` |
| Audit | VERIFIED | Browser *Audit* tab shows each stage event; `test_golden_path.py` checks every stage event and the recorded payable |

## Checks

| Check | State | Result |
|---|---|---|
| Backend tests | VERIFIED | `pytest`: 71 passed |
| Frontend tests | VERIFIED | `e2e` Playwright suite: 10 passed against Docker + PostgreSQL. Any browser console error fails a test. CI runs it in the `docker-smoke` job |
| Lint and type checks | VERIFIED | `ruff check app tests ../scripts`: clean. `npm run build` (`tsc` + Vite): passed |
| RAG evaluation | VERIFIED | `scripts/evaluate.py`: 256/256 checks over 12 claim cases and 21 questions; every refusal correct |
| Adjudication tests | VERIFIED | `test_adjudication.py` plus evaluation amounts 37/37, worked out by hand in `data/evaluation/golden_cases.json` |
| Data provenance | VERIFIED | `scripts/provenance.py --check`: registry has 14 sources and 0 problems; manifest matches the committed copy |
| Security checks | VERIFIED | `pip-audit`: no known vulnerabilities. `npm audit`: 0 in `frontend/` and 0 in `e2e/`. `test_security_guards.py`: throttle, injection. Secret-pattern scan of tracked files: no hits. Headers and upload tests in `test_golden_path.py` |
| Docker smoke test | VERIFIED | `scripts/smoke_test.py http://localhost:8080`: all checks passed on the Compose stack with PostgreSQL 16. A fresh clone also built with `--no-cache` and passed |
| CI | VERIFIED | Every push to pull request #2 runs backend, frontend and Docker smoke jobs; recorded in `IMPLEMENTATION_STATUS.md` |
| Deployment smoke test | BLOCKED | No cloud account here. The environment's cloud variables are proxy placeholders, and `gcloud` has no credentialed account. `render.yaml` and the Azure workflow are ready |

## Areas

| Area | State | Note |
|---|---|---|
| Golden path, review, audit, dashboard | VERIFIED | See above |
| Policy PDF ingestion with processing states | VERIFIED | `test_policy_ingestion.py`; earlier browser run on Docker (screenshot 15) |
| Decision letters, settlement clock, CSV export | VERIFIED | `test_letters_sla.py`; browser letter and CSV download |
| Phone layout | VERIFIED | Browser at 390 px: navigation behind a menu, no sideways scrolling |
| Cloud deployment and deployed smoke test | BLOCKED | Needs the owner to merge pull request #2 and connect the repository on Render, or to add Azure credentials |
| LLM-written answers | BLOCKED | No `ANTHROPIC_API_KEY`. Extractive, cited answers work without it, and the LLM never computes amounts or decides |
| Public 2024–2026 datasets | BLOCKED | Registered with provenance, but not downloaded and their licences not reviewed |
| SSO and user management, OCR, embedding retriever, ML fraud model, background jobs, managed search, Key Vault, Application Insights, property and travel lines | POST_MVP | Listed in the README roadmap |

## How to repeat

```bash
cd backend && ruff check app tests ../scripts && python -m pytest -q
python3 scripts/evaluate.py && python3 scripts/provenance.py --check
cd frontend && npm run build
docker compose up --build -d
cd e2e && npm ci && npx playwright install chromium && npx playwright test   # needs a freshly seeded stack
python3 scripts/smoke_test.py http://localhost:8080
```

After deploying: `python3 scripts/smoke_test.py https://<service> <DEMO_PASSWORD>`. Then `cd e2e && BASE_URL=https://<service> DEMO_PASSWORD=<…> npx playwright test`. Only then record the deployment as VERIFIED.
