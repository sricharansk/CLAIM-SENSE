# Final validation report — Claim Sense MVP

Blueprint Prompt 20. First checked on branch `claude/project-thread-lu5h1l` (pull request #2) on 2026-10-09; re-run on 2026-10-12 on branch `claude/serene-goldberg-dbnoym` after adding the property and travel lines. Figures below are from the 2026-10-12 run.

**Bottom line:** the MVP works end to end on Docker with PostgreSQL. Every check below was run. It is deployed on Render at https://claim-sense.onrender.com, and the smoke test passed against it on 2026-10-12 ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)).

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
| RAG | VERIFIED | Evaluation: retrieval 91/91, hit@1 100%, MRR 1.00; RAG manifest has 85 chunks from 5 wordings, 0 rejected |
| Evidence | VERIFIED | Evaluation: citations 67/67, groundedness 113/113; browser *Policy & evidence* tab; smoke `citations` (13 items) |
| Coverage | VERIFIED | Evaluation: coverage 79/79; browser rejection cites §3.3 |
| Adjudication | VERIFIED | Browser and smoke: ₹64,080 payable on ₹78,000 billed; evaluation amounts 95/95; `test_adjudication.py` (7 hand calculations); `test_property_travel.py`; browser and smoke file a property claim (₹3,47,500) and a travel claim (₹95,000) |
| Risk | VERIFIED | Evaluation: risk 44/44; `test_security_guards.py` (planted-instruction signal) |
| Recommendation | VERIFIED | Browser: *Partial approval*; evaluation: workflow 123/123 |
| Human review | VERIFIED | Browser: approve, approval-limit block, take and release a task; `test_auth.py`; `test_review_assignment.py` |
| Decision | VERIFIED | Browser: status *Approved* and a settlement letter for INR 64,080.00; smoke `human review` |
| Audit | VERIFIED | Browser *Audit* tab shows each stage event; `test_golden_path.py` checks every stage event and the recorded payable |

## Checks

| Check | State | Result |
|---|---|---|
| Backend tests | VERIFIED | `pytest`: 108 passed |
| Frontend tests | VERIFIED | `e2e` Playwright suite: 11 passed against Docker + PostgreSQL. Any browser console error fails a test. CI runs it in the `docker-smoke` job |
| Lint and type checks | VERIFIED | `ruff check app tests ../scripts`: clean. `npm run build` (`tsc` + Vite): passed |
| RAG evaluation | VERIFIED | `scripts/evaluate.py`: 612/612 checks over 41 claim cases and 26 questions; every refusal correct |
| Adjudication tests | VERIFIED | `test_adjudication.py` and `test_property_travel.py` plus evaluation amounts 95/95, worked out by hand in `data/evaluation/golden_cases.json` |
| Data provenance | VERIFIED | `scripts/provenance.py --check`: registry has 14 sources and 0 problems; manifest matches the committed copy |
| Security checks | VERIFIED | `pip-audit`: no known vulnerabilities. `npm audit`: 0 in `frontend/` and 0 in `e2e/`. `test_security_guards.py`: throttle, injection. Secret-pattern scan of tracked files: no hits. Headers and upload tests in `test_golden_path.py` |
| Docker smoke test | VERIFIED | `scripts/smoke_test.py http://localhost:8080`: all checks passed on the Compose stack with PostgreSQL 16. A fresh clone also built with `--no-cache` and passed |
| CI | VERIFIED | Every push to pull request #2 runs backend, frontend and Docker smoke jobs; recorded in `IMPLEMENTATION_STATUS.md` |
| Deployment smoke test | VERIFIED | **Verify deployment** workflow against https://claim-sense.onrender.com: all smoke checks passed, including the health (₹64,080), property (₹3,47,500) and travel (₹95,000) claims ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)). `render.yaml` and the Azure workflow are ready |

## Areas

| Area | State | Note |
|---|---|---|
| Golden path, review, audit, dashboard | VERIFIED | See above |
| Property and travel lines | VERIFIED | 7 seeded claims and 3 evaluation packets with hand-worked amounts; all 42 claim packets run through the API in `reports/claims_results.md`; screenshots 20–22 |
| Policy PDF ingestion with processing states | VERIFIED | `test_policy_ingestion.py`; earlier browser run on Docker (screenshot 15) |
| Decision letters, settlement clock, CSV export | VERIFIED | `test_letters_sla.py`; browser letter and CSV download |
| Phone layout | VERIFIED | Browser at 390 px: navigation behind a menu, no sideways scrolling |
| Cloud deployment and deployed smoke test | VERIFIED | Render, deployed from `main`; Azure needs credentials and is not set up |
| LLM-written answers | PARTIAL | The Render service has an Anthropic key (`llm: anthropic`); the golden evaluation runs with the LLM off, so written answers are not scored. The LLM never computes amounts or decides |
| Public 2024–2026 datasets | BLOCKED | Registered with provenance, but not downloaded and their licences not reviewed |
| SSO and user management, OCR, embedding retriever, ML fraud model, background jobs, managed search, Key Vault, Application Insights, commercial lines | POST_MVP | Listed in the README roadmap |

## How to repeat

```bash
cd backend && ruff check app tests ../scripts && python -m pytest -q
python3 scripts/evaluate.py && python3 scripts/provenance.py --check
cd frontend && npm run build
docker compose up --build -d
cd e2e && npm ci && npx playwright install chromium && npx playwright test   # needs a freshly seeded stack
python3 scripts/smoke_test.py http://localhost:8080
```

After deploying: `python3 scripts/smoke_test.py https://<service> <DEMO_PASSWORD>`. Then `cd e2e && BASE_URL=https://<service> DEMO_PASSWORD=<…> npx playwright test`, or run the **Verify deployment** workflow with the URL. Only then record the deployment as VERIFIED.
