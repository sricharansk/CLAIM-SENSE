# Changelog

Implementation history of Claim Sense, built from `git log --reverse --format='%h %ad %s' --date=short` and grouped by pull request. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The application reports version `1.0.0` (`backend/app/config.py`); `RELEASE_NOTES.md` describes that release. The repository has no git tags, so earlier groups are named by pull request. Dates are commit author dates.

## [Unreleased] - PR #3 (open)

Branch `claude/project-thread-lu5h1l` after the PR #2 merge.

### Added

- Demo book of 42 more synthetic health and motor claims over 41 new policies, each with a designed outcome. The seeder runs them through the real pipeline, replays their reviewer history through the review service (notes start with `[Seeded demo history]`) and spreads them over eight weeks (`af6b418`, 2026-10-09).
- Interactive dashboard: line-of-business and period filters, clickable tiles and bars that open the matching claims, weekly trend, needs-attention list, open-claim ageing, decline reasons with clauses, workload and amounts by line (`af6b418`).
- Claims list: URL-driven filters, removable filter tags, sortable columns (`af6b418`).
- New claim: **Use the sample packet**, served by `GET /api/v1/demo-packet` (`af6b418`).
- How to use screen (`/guide`) and `docs/USER_GUIDE.md` (`af6b418`).
- Travel, home, personal accident and life lines (`d3a26e0`, 2026-10-11):
  - rules engine: an indemnity model for travel and home (covered categories, depreciation, per-item and per-category limits, the average clause, deductible) and a benefit-schedule model for personal accident and life (percent of sum insured, disablement table, weekly benefit, capped reimbursement), all `Decimal` with a clause on every step;
  - pipeline: new document types and fields, accident-only cover, time-limited exclusions (life suicide clause), per-product early-claim window;
  - synthetic wordings `TRV-GLOBE`, `HOME-SHIELD`, `PA-SECURE` and `LIFE-TERM` 2026.1 with 36 policies, 35 demo-book claims and four evaluation packets.
- The UI handles all six lines (this change): claim type, dashboard and claims-list line filters and line labels follow `LINES` in `frontend/src/api.ts`; `GET /api/v1/insured-policies` returns `line_of_business`, so choosing a policy sets the claim type; a sample packet per line (`GET /api/v1/demo-packet?line=…`, packets in `data/claims/demo_upload/<line>/`).
- Golden evaluation cases C13–C16 (travel, home, personal accident, life) and more assistant questions; the committed report records 365 / 365 checks over 16 claim cases and 30 questions (this change).
- A 10,000-claim synthetic portfolio over all six lines (`data/synthetic/claims_portfolio_full.csv`); the dashboard shows rule precision and recall per line and per injected pattern (`portfolio_full` in `/analytics`) (this change).
- CAS Schedule P industry benchmark: `scripts/fetch_public_data.py` downloads the CAS Loss Reserving Database, checks its SHA-256 and commits only aggregates to `data/public/cas_schedule_p/benchmark.json`; registry entry `cas-schedule-p-1998-2007`; `GET /api/v1/benchmarks/industry`; shown on the Data sources screen (this change).
- VS Code setup in `.vscode/` (recommended extensions, Run and Debug configurations including a full-stack compound, numbered setup, run, test and Docker tasks with Windows variants) and a *Run it in VS Code* guide in the README (this change).
- Browser tests for a travel sample packet and for the benchmark and six-line portfolio (13 in all) (this change).
- Documents required by the blueprint (PART 2): `docs/UX_FLOWS.md`, `docs/API.md`, `docs/ENVIRONMENT.md`, `docs/ERROR_HANDLING.md`, `docs/OBSERVABILITY.md`, `docs/ROADMAP.md` and this changelog (this change).

### Changed

- Dashboard totals show whole rupees; claim-level amounts keep paise (this change).
- The sign-in screen pre-fills the default password only when the deployment still uses it (`GET /api/v1/auth/demo-info`) (`af6b418`).
- Policy assistant: an off-topic question must share two specific terms with a clause before it is answered; a few lay synonyms added (`d3a26e0`).

## [1.0.0] - 2026-10-09 - PR #2 (merged into main, `a1a93ac`)

Letters, evaluation, PDF ingestion, review assignment, fact correction and data provenance.

### Added

- Decision letters (settlement, repudiation, document request, under review) from templates and stored data, quoting the clause; settlement clock from the policy's settlement clause; claim register CSV export (`4695c27`, 2026-10-08).
- Golden evaluation suite: `scripts/evaluate.py` runs claim cases and policy questions on a fresh database and writes `reports/evaluation.{json,md}`; CI runs it and uploads the report (`df98698`).
- Evaluation screen and `GET /api/v1/evaluation`; the image ships `reports/` (`d7f61a3`).
- Sign-in throttle (429 with `Retry-After`, audited as `LOGIN_THROTTLED`); embedded-instruction scan of uploaded documents raising the `EMBEDDED_INSTRUCTIONS` risk signal; override and escalation rates on the dashboard (`40ba8c2`).
- Policy wording ingestion from PDF or Markdown with SHA-256 duplicate check and recorded processing states in `policy_ingestions`; ingestion history in the policy library (`5a0ecf9`).
- Claim workspace split into eight tabs with counts, deep links and empty states (`15f8ee5`).
- PRD, design system, database, code style, testing and release-readiness documents (`8294dc3`).
- Review queue with risk, age and assignee; take, release and reassign (`POST /api/v1/reviews/{task}/assign`), audited as `TASK_ASSIGNED` / `TASK_RELEASED` (`4e3be3f`).
- Data provenance: `data/source_registry.json`, validator, RAG manifest tracing every chunk to file, version, page, clause and extraction run; Data sources screen; `scripts/provenance.py --check` in CI (`b3e46c1`).
- Audit events for every pipeline stage with the analysis correlation ID (`aee1732`).
- Reviewer correction of extracted facts (`POST /api/v1/claims/{n}/facts`), audited as `FACT_CORRECTED` (`0154dc6`).
- Phone layout: sidebar collapses into a menu below 980 px (`a1c5ece`).
- Playwright browser suite run in CI against Docker + PostgreSQL (`68b1516`).
- Final validation report and release notes (`170ed76`).
- Deploy to Render link and deployment steps (`2e2ce10`).
- Verify deployment workflow that checks a deployed URL from GitHub Actions (`30105b8`).

### Changed

- Smoke test also checks the served frontend, ingestion records and the evaluation report (`91ed4aa`).
- Screenshots refreshed from Docker + PostgreSQL runs (`f13711a`, `27a874a`); evaluation report regenerated from the current code (`29693e6`).

### Fixed

- Assistant misses found by the evaluation: ICU synonym, phrase synonyms, refusal when only generic insurance words overlap (`df98698`).
- The provenance check points at its own database before importing the app, so it cannot read a developer database (`ba56e98`).

### Security

- Playwright pinned to 1.56.1 (1.49.1 is affected by GHSA-7mvr-c777-76hp) (`af18f9d`).

## PR #1 - 2026-10-09 (merged into main, `d1368ce`)

Working golden path from claim intake to human decision.

### Added

- FastAPI backend with a supervisor and bounded agents (intake, document intelligence, policy retrieval, coverage, adjudication tool, risk/fraud, evidence, review/workflow, audit), with persisted runs and tool calls (`119b65a`, 2026-10-08).
- Hybrid clause retrieval (BM25 + character n-gram TF-IDF, RRF) with page, section and clause citations and refusal on weak evidence (`119b65a`).
- Deterministic `Decimal` adjudication with a cited waterfall (`119b65a`).
- React + TypeScript UI: dashboard, claims, intake and upload, claim analysis, human review, review queue, policy library, assistant, audit, data sources (`119b65a`).
- Synthetic policies (two health versions, motor), 8 golden claim packets, a 1,000-claim portfolio with injected anomaly labels (`119b65a`).
- Docker image, Compose stack with PostgreSQL, smoke test, CI, Azure Container Apps workflow and Render blueprint (`119b65a`).
- Sign-in with PBKDF2 password hashes and signed expiring tokens; adjuster, supervisor and auditor accounts; approval limit and escalation; role-aware UI (`ebd7f51`).

### Security

- Upgraded flagged backend and frontend dependencies; security headers and a strict CSP; `pip-audit` and `npm audit` in CI (`c499e47`).

## Initial upload - 2026-10-07

### Added

- `PROJECT 1.MD`, the original project prompt (`6d772a7`).
