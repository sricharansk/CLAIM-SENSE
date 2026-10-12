# Implementation Status

Last updated: 2026-10-12 (deployment verified). Source of truth: `docs/Claim_Sense_Project_1_..._FINAL_V2_..._Deployment_Ready.md` and `PROJECT_1_FINAL_CONTENTS.md`.

## Starting point

The repository held one file, `PROJECT 1.MD` (the original project prompt). There was no code, build, test, Docker or deployment configuration. Everything below was built in this pass.

## Completed (validated)

| # | Golden-path step | Implementation | Validation |
|---|---|---|---|
| 1 | Dashboard | `frontend/src/pages/Dashboard.tsx`, `GET /api/v1/analytics` | Browser run, screenshot `docs/screenshots/01-dashboard.png` |
| 2 | Claim creation and document upload | `POST /claims`, `POST /claims/{n}/documents`, `NewClaim.tsx` | Browser upload of `data/claims/demo_upload`, API test |
| 3 | Extraction and structured facts | `agents/document.py` (PDF via pypdf, text), facts with file/line/confidence; `POST /claims/{n}/facts` records a reviewer correction with a reason (blueprint section 'New Claim'), the next analysis uses it (`intake.consolidate`: latest correction, then the first document value), the extracted value is kept and shown, `FACT_CORRECTED` audited; bill totals and line items are not correctable | `test_extraction.py` incl. PDF; `test_fact_correction.py`; browser correction and re-run, 0 console errors |
| 4 | Policy and version matching | `agents/policy.py`, effective-dated `policy_versions` | `test_version_matching_uses_wording_in_force` |
| 5 | Hybrid RAG | `rag/retriever.py` BM25 + char n-gram TF-IDF, RRF, synonym expansion | `test_rag.py` |
| 6 | Evidence with source metadata | clause ref, section, page, version, file on every citation | `test_rejection_cites_clause`, smoke test |
| 7 | Coverage and exclusions | `agents/coverage.py` | 34 golden scenarios; every exclusion, waiting period and loss-dependent document has a claim |
| 8 | Deterministic adjudication | `adjudication/rules.py` (Decimal, waterfall) | `test_adjudication.py` hand calculations |
| 9 | Fraud/risk signals | `agents/risk.py` | `test_risk_levels`, duplicate test, portfolio evaluation |
| 10 | Evidence-backed recommendation | `agents/evidence.py` | 34 golden scenarios |
| 11 | Human review and workflow | `agents/review.py`, `/review`, `/reviews`; queue shows status, risk, age, priority and assignee (blueprint Prompt 13); `POST /reviews/{task}/assign`: adjusters take and release their own tasks, supervisors reassign, adjusters cannot take supervisor-queue tasks or decide a claim assigned to someone else; `TASK_ASSIGNED`/`TASK_RELEASED` audited | API test incl. validation and override audit; `test_review_assignment.py`; browser take, release and supervisor reassign, 0 console errors |
| 12 | Audit trail | `audit_events`, `/audit`; every pipeline stage is audited (blueprint Prompt 14): `CLAIM_CREATED`, `DOCUMENT_UPLOADED`, `ANALYSIS_STARTED`, `FACTS_EXTRACTED`, `POLICY_SELECTED`, `EVIDENCE_RETRIEVED`, `COVERAGE_ANALYZED`, `ADJUDICATION_CALCULATED`, `RISK_SCORED`, `EVIDENCE_PACKAGED`, `AI_RECOMMENDATION`, `TASK_ASSIGNED`/`TASK_RELEASED`, `HUMAN_DECISION` (marked `final` for approve and reject), with the correlation ID of the analysis run | `test_golden_path.py` checks every stage event and the payable amount recorded; browser |
| 13 | Interactive frontend | 11 screens (sign-in, dashboard, claims, new claim, claim workspace with 8 tabs, review queue, policy library, assistant, audit, evaluation, data sources), all calling real endpoints; below 980 px the sidebar collapses into a Menu button | Playwright golden path: 0 console errors; at 390 px wide no page scrolls sideways (dashboard, claims, claim, review queue) |
| – | Supervisor/orchestrator | `agents/supervisor.py`, `analysis_runs`, `agent_runs` with tool calls | Safe-failure and re-run tests |
| – | Docker | `Dockerfile` (UI + API in one image), `docker-compose.yml` with PostgreSQL | Built and run locally on PostgreSQL; smoke test passed |
| – | CI | `.github/workflows/ci.yml`: ruff, pytest, golden evaluation, pip-audit, npm audit, frontend build, Docker + PostgreSQL smoke test; `verify-deployment.yml` (manual) checks a deployed URL: readiness, smoke test, optional browser suite | All runs on PR #1 passed; PR #1 merged to `main` 2026-10-08 |
| – | Golden evaluation (blueprint Prompt 17) | `app/evaluation.py`, `scripts/evaluate.py`, cases in `data/evaluation/` (41 claim cases across four lines covering all 10 required types, 26 assistant questions), report in `reports/evaluation.{json,md}`, `/evaluation` screen | 612 / 612 checks; CI fails on any failed check; `test_evaluation.py`; browser run, screenshot `13-evaluation.png` |
| – | Sign-in and roles | `auth.py`, `/auth/login`, `/auth/me`; adjuster / supervisor / auditor; approval limit and escalation rules; sign-in screen and role-aware UI | `test_auth.py` (7 tests); browser run signs in and sees approval blocked over the limit |
| – | Policy PDF ingestion (blueprint Prompt 05) | `services.ingest_policy_file`: upload → validation → SHA-256 checksum (duplicate refused) → page-preserving PDF extraction (pypdf) or Markdown → section/clause parsing (`rag/parser.parse_policy_pages`) → version metadata → persistence → indexing; states UPLOADED, VALIDATING, EXTRACTING, INDEXING, READY, FAILED recorded per attempt in `policy_ingestions`; instruction-like lines reported as warnings; `/policy-ingestions`; Policy library shows the stages and history | `test_policy_ingestion.py` (PDF of 6 pages → 21 clauses with page numbers, citations name the PDF, duplicate, scanned PDF, unreadable PDF, wrong type, supervisor-only); browser run on Docker ingests `data/policies/ingest_demo/HLT-SHIELD_2026.1.pdf`, screenshot `15-policy-pdf-ingestion.png` |
| – | Claim workspace tabs (blueprint Prompt 15) | `ClaimDetail.tsx`: Overview, Documents, Policy & evidence, Coverage, Adjudication, Risk, Review, Audit, with counts and deep links (`/claims/CLM-H-1002#coverage`); empty states when no analysis yet; "Open review" prompt while a decision is pending | `npm run build`; browser run uses every tab; screenshots `02`–`06`, `16-claim-evidence.png` |
| – | Data provenance (blueprint Data Prompts A and G) | `data/source_registry.json` (14 sources: 5 synthetic in use with SHA-256 over their files, 9 public sources registered, not downloaded); `provenance.py` validator rejects missing provenance, unconfirmed licences on in-use data and checksum drift; RAG manifest (`/knowledge-base/manifest`, `reports/rag_manifest.json`) resolves every indexed chunk to source file, version, page, section/clause and extraction run; the index keeps out chunks that do not resolve; Data sources screen shows both; `docs/DATA_PROVENANCE.md` | `test_provenance.py` (6); `scripts/provenance.py --check` in CI (85 chunks from 5 wordings, 0 rejected, manifest reproducible); smoke test against Docker + PostgreSQL (14 sources, 0 problems; 85 chunks, 0 rejected); browser run, 0 console errors, screenshot `17-data-provenance.png` |
| – | Property and travel lines | HOME-GUARD 2025.1 and TRV-GLOBE 2025.1 wordings and terms (`data/synthetic/generate.py`); `rules.adjudicate_property` (contents depreciation 2.2, average clause 2.3 with 15% tolerance, excess 4.1, sum insured cap 1.2) and `rules.adjudicate_travel` (non-payable items 2.4, per-item and per-benefit limits 2.2/2.3, deductible 4.1, cap 1.2); coverage checks the trip period (1.3) and documents that depend on the loss (police report, airline irregularity report, medical report); per-line item categories; travel risk ignores early-claim; 7 seeded claims, 3 evaluation packets; New Claim offers all four lines | `test_property_travel.py` (11); evaluation C13–C22 with hand-worked amounts; smoke test files a property (₹3,47,500) and travel (₹95,000) claim; browser test files both from the UI; screenshots `20`–`22` |
| – | Results on every claim | `scripts/claims_report.py` runs all 42 claim packets (34 seeded, 7 evaluation, demo upload) through the API on a fresh database and writes `reports/claims_results.{json,md}`: per-claim outcome, clause, risk and queue, totals by line, deductions by rule, portfolio risk-rule results | Run 2026-10-12: 23 claims, ₹35,29,100 billed, ₹23,17,150 recommended payable, every claim routed to human review |
| – | Settlement clock | `sla.py`: due date from the `settlement_days` term (clause 6.3 health, 4.3 motor), counted from the last document; shown on claim page, claims list, review queue and dashboard | `test_letters_sla.py`; browser run |
| – | Decision letters | `letters.py`, `GET /claims/{n}/letter`: settlement, repudiation (quotes the clause), document request, under review; deterministic, marked draft until a human decides | `test_letters_sla.py`; browser run generates the ₹64,080.00 settlement letter; screenshot `12-rejection-letter.png` |
| – | CSV export | `GET /claims-export.csv`, Export CSV button on `/claims` | `test_letters_sla.py`; browser download |
| – | Sign-in throttle and injection guard (blueprint Prompt 16) | `auth.LoginThrottle` (429 + `Retry-After`), `safety.py` scan in the Intake Agent, `EMBEDDED_INSTRUCTIONS` risk signal; assistant refusal gate | `test_security_guards.py`: 5 failures then 429; injected discharge summary is flagged HIGH, routed to investigation, payable unchanged at ₹64,080 |
| – | Override and escalation rates (blueprint Prompt 14) | `analytics.dashboard`: override rate, amount overrides, escalation rate, reviewer actions; dashboard KPIs | `test_dashboard_reports_override_and_escalation_rates` |
| – | Security | Upload allow-list, size limit and filename sanitising; security headers and CSP; non-root container; dependency audits; see `docs/SECURITY.md` | Header and path tests; pip-audit and npm audit clean |

## Validation results (2026-10-12, every rule exercised)

- **Audit of the four wordings.** Every exclusion, waiting period, limit and loss-dependent document in the structured terms was checked for a claim that exercises it. Found and fixed:
  - **Gap fixed: the health pre-existing disease waiting period (§3.2) was in the terms but not enforced**, so such a claim would have been paid. `coverage.py` now applies it when the documents say a condition was pre-existing, declared at proposal or a known case, and cover has run less than the period (36 months in 2025.1, 48 in 2024.1).
  - **Gap fixed: motor §4.1 requires a police report for theft or malicious damage**; the motor terms now list it as a document that depends on the loss.
  - 15 seeded claims added, one per rule that had none: health cosmetic (§4.1), alcohol (§4.2), experimental (§4.5), 30-day initial wait (§3.1), pre-existing disease (§3.2); motor wear and tear (§3.3), outside India (§3.4), engine above 1500cc (₹3,500 deductible, §2.3), malicious damage without a police report; property wilful act (§3.2), act of war (§3.4), loss above the sum insured (cap, §1.2); travel alcohol (§3.3), against medical advice (§3.4), medical claim without the doctor's report. Golden cases C27–C41 with hand-worked results. The 19 earlier seeded claims give identical results.
  - The evaluation found one retrieval miss (the Nepal claim did not retrieve "outside India" §3.4); fixed by mapping Nepal and Bhutan to that wording in `rag/retriever.py`.
- `ruff`: clean. `pytest`: 108 passed. `python scripts/evaluate.py`: 612 / 612 checks over 41 claim cases and 26 questions. `python scripts/provenance.py --check`: passed. `python scripts/claims_report.py`: 42 claims, every one routed to a human queue.

## Validation results (2026-10-12, deployment and remaining claims)

- **Cloud deployment verified.** Render serves `main` at https://claim-sense.onrender.com. The **Verify deployment** workflow passed every smoke check against it ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)): frontend, health, readiness, sign-in required, sign-in, 15 seeded claims, 4 wordings ready in the ingestion log, evaluation report 405/405, source registry and RAG manifest (85 chunks, 0 rejected), golden health claim (₹64,080, partial approval, 13 evidence items, approved, 14 audit events), property claim ₹3,47,500, travel claim ₹95,000, cited answer and refusal. That run was against commit `37fd020`; this change set redeploys when merged. The first four runs failed at sign-in because no `DEMO_PASSWORD` repository secret existed and the service uses a custom password; adding the secret fixed it. The service reports `llm: anthropic`, so an Anthropic key is set on Render.
- Four seeded claims added for clauses no claim exercised: `CLM-H-1007` maternity (§4.4), `CLM-M-2003` expired licence (§3.2), `CLM-P-3004` unoccupied home (§3.3), `CLM-T-4005` pre-existing condition (§3.1). New policies, so no earlier claim's risk or sum insured changes; the 15 earlier seeded claims give identical results.
- The 1,000-claim synthetic portfolio now covers all four lines (507 health, 241 motor, 124 property, 128 travel); travel is scored without the early-claim signal, as in the live risk agent. Precision 86.6%, recall 84.1% (TP 58, FP 9, FN 11, TN 922).
- GitHub Actions moved to Node 24 versions (checkout v5, setup-node v5, setup-python v6, upload-artifact v6), removing the Node.js 20 deprecation warning on every run.
- `ruff`: clean. `pytest`: 93 passed. `python scripts/evaluate.py`: 449 / 449 checks over 26 claim cases and 26 questions. `python scripts/provenance.py --check`: 14 sources, 0 problems; 85 chunks, 0 rejected. `python scripts/claims_report.py`: 27 claims, every one routed to a human queue.

## Validation results (2026-10-12, property and travel lines)

- `ruff check app tests ../scripts`: clean.
- `pytest`: 89 passed (71 before, plus 11 in `test_property_travel.py` and 7 new seeded-scenario cases). Review of the diff found that a reviewer correction of `value_at_risk` was not validated as an amount (a bad value would have crashed the adjudicator); it is now refused with 422, and a valid correction is used by the next analysis.
- `python scripts/provenance.py --check`: registry 14 sources, 0 problems; RAG manifest 85 chunks from 5 wordings, 0 rejected, identical to the committed copy.
- `python scripts/evaluate.py`: 405 / 405 checks over 22 claim cases and 26 questions (retrieval hit@1 100%, MRR 1.00). The first run missed one question ("underinsured" did not reach the Underinsurance clause); fixed with a synonym in `rag/retriever.py`. All 12 earlier cases and 21 earlier questions unchanged.
- The first pipeline run of the new claims found two bugs, both fixed before the evaluation: "Bedroom" matched the furniture word "bed", and the risk agent read a terms key that did not exist, so travel claims still got the early-claim signal.
- `python scripts/claims_report.py`: 23 claims, all analysed and routed to a human queue (`reports/claims_results.md`).
- `npm run build`: passed. `pip-audit`: no known vulnerabilities. `npm audit`: 0 vulnerabilities.
- Docker image built from this branch, Compose stack with PostgreSQL 16 on a fresh volume: `scripts/smoke_test.py http://localhost:8080` all checks passed (including the new property and travel claims, and again on a second run against the same database); `e2e` Playwright suite 11 / 11 passed, 0 console errors.

## Validation results (2026-10-09)

- `ruff check app tests`: clean.
- `pytest`: 71 passed.
- `python scripts/provenance.py --check`: registry 14 sources, 0 problems; RAG manifest 54 chunks from 3 documents, 0 rejected, identical to the committed copy.
- `python scripts/evaluate.py`: 256 / 256 checks passed (retrieval hit@1 100%, MRR 1.00, all refusals correct). The first run found three assistant misses (ICU question cited the room-rent clause, a cataract question cited the 30-day waiting period, two off-topic prompts were answered); fixed in `rag/retriever.py` and `rag/service.py`.
- `npm run build` (tsc + vite): passed.
- `e2e` Playwright suite (10 browser tests) against Docker + PostgreSQL on a fresh volume: 10 passed; runs in CI (`docker-smoke`). Final report: `docs/FINAL_VALIDATION_REPORT.md`; release notes: `RELEASE_NOTES.md`.
- `pip-audit -r backend/requirements.txt`: no known vulnerabilities. `npm audit`: 0 vulnerabilities.
- GitHub Actions CI run 1 on PR #1: backend, frontend and docker-smoke jobs passed.
- Browser (Playwright, Chromium) against Vite dev server and against the Docker image on PostgreSQL: create claim, upload 3 documents, analyse (₹78,000 billed, ₹64,080 payable, partial approval), approve, generate the settlement letter (INR 64,080.00) and a repudiation letter, export CSV, assistant answer and refusal, evaluation scorecard (256 / 256), adjuster escalates the over-limit claim and the dashboard shows escalation rate 50% (1/2) and override rate 0% (0/1), all pages load (2026-10-09, image built from this branch, screenshot `14-dashboard-after-review.png`). No console errors on the Docker run.
- Browser regression on the Docker image with a fresh PostgreSQL volume (2026-10-09, after the review-assignment, provenance, audit, fact-correction and phone-layout stages): golden claim ₹64,080 partial approval, approval-limit block, approve, letters, CSV, assistant answer and refusal, evaluation 256 / 256, escalation and dashboard rates (override 0% (0/1), escalation 50% (1/2)), take / release / reassign a review task, provenance screen (14 sources, 5 / 5 checksums verified, 54 chunks, 0 rejected), fact correction and re-run, phone menu at 390 px. 0 console errors. Screenshots `00`–`14`, `16`–`19` refreshed.
- `scripts/smoke_test.py http://localhost:8080` against Docker + PostgreSQL: all checks passed, including the registry and manifest checks.

## Definition of done (blueprint PART 20)

| Item | State |
|---|---|
| Repository audited; source-of-truth docs created | Done (`PRD.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `DATABASE.md`, `SECURITY.md`, `CODE_STYLE.md`, `TESTING.md`, `AGENTS.md`; release checklist in `RELEASE_READINESS.md`) |
| Backend runs; frontend runs; database migrates; demo data loads | Done (SQLite and PostgreSQL) |
| Policy ingests (PDF and Markdown, with processing states); claim ingests; document extraction | Done |
| Policy/version matching; hybrid RAG; citations resolve | Done |
| Coverage; deterministic adjudication; risk/fraud; supervisor | Done |
| Human review; audit; dashboard | Done |
| Golden tests pass; security checks pass; Docker works; repository clean | Done |
| Deployment succeeds; deployed health check; deployed smoke test | Done: Render, https://claim-sense.onrender.com, all smoke checks passed 2026-10-12 ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)) |

## In progress

Nothing in progress.

## Blocked

| Item | Blocker | What unblocks it |
|---|---|---|
| Azure deployment | Not set up: Render is the live deployment. The Azure workflow is ready but needs Azure credentials | Add `AZURE_CREDENTIALS` and the variables in `DEPLOYMENT.md`, then run the *Deploy to Azure Container Apps* workflow |
| Scoring LLM-written answers | The Render service has an Anthropic key (`llm: anthropic`), but the golden evaluation runs with the LLM off for repeatable results, so written answers are not scored | Add an evaluation mode that runs with the key and checks every quoted sentence against its cited clause |
| Public 2024–2026 datasets | Registered in `data/source_registry.json` with dates, URLs and licence status; not downloaded or ingested (no licence review done; most are `CHECK_SOURCE`) | Confirm terms, download, stamp checksums with `scripts/provenance.py --write`, ingest the IRDAI circulars through the policy ingestion pipeline |

## Not in this version (roadmap)

Single sign-on and user management, OCR for scanned images, embedding retriever, ML fraud model, more property perils and travel benefits (liability, trip delay), background job queue, Azure AI Search, Key Vault, Application Insights, reopening decided claims.

## Next action

Render deploys `main` automatically. After merging a change, run the **Verify deployment** workflow with `https://claim-sense.onrender.com` (it signs in with the `DEMO_PASSWORD` repository secret). This build environment cannot reach `onrender.com`, so verification runs from GitHub Actions.
