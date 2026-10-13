# Claim Sense: "RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant"

**Claim Sense — AI-Powered Insurance Claims Intelligence, Adjudication & Policy Decision-Support Platform**

> AI recommends. Evidence supports. Rules calculate. Humans decide. Workflows execute. Audit trails record.

Claim Sense takes a health, motor, property (home) or travel claim from intake to a human decision. It reads the claim documents, matches the policy wording that was in force on the incident date, retrieves the relevant clauses with page and clause citations, checks coverage and exclusions, calculates the payable amount with deterministic rules, raises risk and fraud signals, and hands an evidence-backed recommendation to a human reviewer. Every step is recorded in an audit trail.

**Live demo:** https://claim-sense.onrender.com (Render free tier; the first request after a quiet spell can take a minute while the service wakes). Verified on 2026-10-12 by the **Verify deployment** workflow: every smoke check passed ([run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)).

All policies, people and claims in this repository are **synthetic**. See [Data](#data-and-datasets).

![Dashboard](docs/screenshots/23-dashboard-interactive.png)

## What works today

| Area | What you can do | Where |
|---|---|---|
| Sign-in and roles | Adjuster (approves up to ₹2,00,000), Supervisor (no limit, decides escalations, ingests policies), Auditor (read-only); signed tokens; every action audited under the signed-in user | `/` |
| Dashboard | Totals by line of business; every tile, line and bar opens the matching claims (filters by line, recommendation, risk or status, removable as chips); live claim counts, recommendations, risk mix, override and escalation rates, reviewer actions, settlement clock, portfolio evaluation | `/` |
| Claim intake | Create a claim, upload PDF or text documents, run the agent pipeline | `/claims/new` |
| Document intelligence | Document classification, extracted facts with source file, line and confidence, itemised charges; reviewers correct a fact with a reason before (re-)running the analysis, the extracted value is kept and the correction audited | claim page |
| Lines of business | Health (HLT-SHIELD), motor (MTR-SECURE), property / home (HOME-GUARD) and overseas travel (TRV-GLOBE), each with its own synthetic wording, structured terms and rules | `/policies` |
| Policy versioning | Picks the wording version in force on the incident date (HLT-SHIELD 2024.1 vs 2025.1) | claim page |
| Hybrid RAG | BM25 + character n-gram vectors fused with reciprocal rank fusion; clause, section and page citations; refuses when evidence is weak | `/assistant` |
| Coverage | Policy period, trip period (travel), initial and specified-disease waiting periods, exclusions, required documents including those that depend on the loss (police report for burglary, airline report for lost baggage, medical report for treatment abroad), each citing its clause | claim page |
| Adjudication | Decimal rules engine: non-payable items, per-day limits, depreciation (motor parts, home contents), average clause for underinsured homes, per-item and per-benefit travel limits, deductible or excess, co-pay, sum-insured cap, shown as a waterfall | claim page |
| Risk / fraud | Transparent weighted signals: amount ratio, early claim, frequency, duplicates, amount and name mismatches, missing documents, text in documents addressed to an AI | claim page |
| Recommendation | Approve, partial approval, reject, request info or investigate, with reasons and an evidence package | claim page |
| Human review | Approve (with amount override), reject, request info, investigate, escalate; notes required for adverse actions; approval limits enforced; escalated claims need a supervisor | claim page, `/reviews` |
| Workflow | Routing to adjuster, investigation (SIU), pending-information and supervisor queues; queue shows status, risk, age and assignee; adjusters take and release tasks, supervisors reassign | `/reviews` |
| Settlement clock | Due date from the policy's settlement clause (30 days after the last document, clause 6.3 health / 4.3 motor / 5.3 property and travel); on track, due soon, overdue, met or breached | claim page, `/claims`, `/reviews`, `/` |
| Decision letters | Settlement, repudiation (quotes the clause relied on), document-request and under-review letters built from data, no LLM; printable; marked draft until a human decides | claim page |
| Export | Download the claim register as CSV with decision, payable amount, risk and settlement status | `/claims` |
| Golden evaluation | 57 hand-worked claim cases across all four lines (all 10 required types) and 26 assistant questions scored on retrieval, citations, groundedness, coverage, amounts, risk and workflow; CI fails on any miss | `/evaluation`, `reports/evaluation.md` |
| Audit | Append-only events with actor, details and correlation IDs | `/audit` |
| Policy library | Browse clauses by version, view structured terms, ingest new wordings as PDF or Markdown with checksum, page-preserving extraction and visible processing states (Uploaded → Validating → Extracting → Indexing → Ready / Failed) | `/policies` |
| Provenance | Source registry with publisher, dates, licence, intended use and SHA-256 checked on every request; RAG manifest tracing every indexed chunk to file, version, page, clause and extraction run; chunks without provenance are kept out of the index | `/datasets`, [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) |

## Real results from the golden scenarios

These are the outputs the running system produces for the 50 seeded scenarios, one or more for every exclusion, waiting period, limit and loss-dependent document in the four wordings, plus the common payable situations on every line and a lapsed policy (no hand-edited numbers; `backend/tests/test_golden_path.py` asserts the recommendations and `reports/evaluation.md` the amounts). [reports/claims_results.md](reports/claims_results.md) has all 58 claim packets in the repository, totals by line and where the money went; regenerate it with `python3 scripts/claims_report.py`. The deployed app starts with 57 of them already analysed (the 50 scenarios and the 7 evaluation packets); the demo upload is the one you file yourself.

| Claim | Scenario | Wording | Claimed | Payable | Coverage | Risk | Recommendation |
|---|---|---|---:|---:|---|---|---|
| CLM-H-1001 | Appendicectomy with room-rent cap, consumables, deductible, co-pay | HLT-SHIELD v2025.1 | ₹1,06,600 | ₹84,330 | Covered | Low | Partial approval |
| CLM-H-1002 | Cataract 6 months into a 24-month specified-disease wait | HLT-SHIELD v2025.1 | ₹61,500 | ₹0 | Not covered (§3.3) | Low | Reject |
| CLM-H-1003 | ICU pneumonia, 50 days after start, 94% of sum insured, form ≠ bill | HLT-SHIELD v2025.1 | ₹4,68,000 | ₹3,32,100 | Covered | High (75) | Investigate |
| CLM-H-1004 | Dengue, discharge summary missing | HLT-SHIELD v2025.1 | ₹43,400 | ₹34,560 | Covered | Low | Request info |
| CLM-H-1005 | Fracture in Feb 2025, so the 2024.1 wording applies | HLT-SHIELD v2024.1 | ₹76,500 | ₹50,800 | Covered | Low | Partial approval |
| CLM-H-1006 | Resubmission of CLM-H-1001 | HLT-SHIELD v2025.1 | ₹1,06,600 | ₹84,330 | Covered | High (50) | Investigate |
| CLM-M-2001 | Rear-end collision, 34-month-old car | MTR-SECURE v2025.1 | ₹73,500 | ₹55,350 | Covered | Low | Partial approval |
| CLM-M-2002 | Breath analyser positive | MTR-SECURE v2025.1 | ₹65,500 | ₹0 | Not covered (§3.1) | Low | Reject |
| CLM-P-3001 | Kitchen fire; home worth ₹30 lakh insured for ₹25 lakh | HOME-GUARD v2025.1 | ₹4,50,000 | ₹3,47,500 | Covered | Low | Partial approval |
| CLM-P-3002 | Burglary: laptop, TV and unscheduled gold jewellery | HOME-GUARD v2025.1 | ₹3,05,000 | ₹1,25,600 | Covered | Low | Partial approval |
| CLM-P-3003 | Seepage and gradual deterioration | HOME-GUARD v2025.1 | ₹83,000 | ₹0 | Not covered (§3.1) | Low | Reject |
| CLM-T-4001 | Emergency appendicectomy in Singapore | TRV-GLOBE v2025.1 | ₹4,42,500 | ₹4,34,000 | Covered | Low | Partial approval |
| CLM-T-4002 | Lost checked baggage above per-item and per-trip limits | TRV-GLOBE v2025.1 | ₹1,81,000 | ₹95,000 | Covered | Low | Partial approval |
| CLM-T-4003 | Paragliding injury in Switzerland | TRV-GLOBE v2025.1 | ₹2,01,000 | ₹0 | Not covered (§3.2) | Low | Reject |
| CLM-T-4004 | Lost baggage, no airline irregularity report | TRV-GLOBE v2025.1 | ₹43,000 | ₹38,000 | Covered | Low (10) | Request info |
| CLM-H-1007 | Caesarean delivery | HLT-SHIELD v2025.1 | ₹77,500 | ₹0 | Not covered (§4.4) | Low | Reject |
| CLM-M-2003 | Driver's licence expired before the accident | MTR-SECURE v2025.1 | ₹58,500 | ₹0 | Not covered (§3.2) | Low | Reject |
| CLM-P-3004 | Burglary after the home was unoccupied for about 95 days | HOME-GUARD v2025.1 | ₹1,72,000 | ₹0 | Not covered (§3.3) | Low | Reject |
| CLM-T-4005 | Heart condition under treatment before departure | TRV-GLOBE v2025.1 | ₹2,78,000 | ₹0 | Not covered (§3.1) | Low | Reject |
| CLM-H-1008 | Rhinoplasty for appearance | HLT-SHIELD v2025.1 | ₹83,000 | ₹0 | Not covered (§4.1) | Low | Reject |
| CLM-H-1009 | Head injury while intoxicated | HLT-SHIELD v2025.1 | ₹28,000 | ₹0 | Not covered (§4.2) | Low | Reject |
| CLM-H-1010 | Investigational stem cell therapy | HLT-SHIELD v2025.1 | ₹2,11,000 | ₹0 | Not covered (§4.5) | Low | Reject |
| CLM-H-1011 | Typhoid 14 days after the policy started | HLT-SHIELD v2025.1 | ₹32,000 | ₹0 | Not covered (§3.1) | Low (20) | Reject |
| CLM-H-1012 | Diabetes declared at proposal, 14 months into cover | HLT-SHIELD v2025.1 | ₹57,000 | ₹0 | Not covered (§3.2) | Low | Reject |
| CLM-M-2004 | Engine seizure, mechanical breakdown | MTR-SECURE v2025.1 | ₹77,000 | ₹0 | Not covered (§3.3) | Low | Reject |
| CLM-M-2005 | Collision while driving in Nepal | MTR-SECURE v2025.1 | ₹59,000 | ₹0 | Not covered (§3.4) | Low | Reject |
| CLM-M-2006 | SUV above 1500cc: depreciation and ₹3,500 deductible | MTR-SECURE v2025.1 | ₹82,000 | ₹56,100 | Covered | Low | Partial approval |
| CLM-M-2007 | Malicious damage, no police report | MTR-SECURE v2025.1 | ₹33,000 | ₹26,500 | Covered | Medium (30) | Request info |
| CLM-P-3005 | Fire deliberately set by the insured | HOME-GUARD v2025.1 | ₹1,43,000 | ₹0 | Not covered (§3.2) | Low | Reject |
| CLM-P-3006 | House destroyed after lightning: capped at sum insured | HOME-GUARD v2025.1 | ₹11,60,000 | ₹10,00,000 | Covered | Medium (30) | Partial approval |
| CLM-P-3007 | Damage recorded as an act of war | HOME-GUARD v2025.1 | ₹1,07,000 | ₹0 | Not covered (§3.4) | Low | Reject |
| CLM-T-4006 | Fall while intoxicated abroad | TRV-GLOBE v2025.1 | ₹1,14,000 | ₹0 | Not covered (§3.3) | Low | Reject |
| CLM-T-4007 | Trip against medical advice after surgery | TRV-GLOBE v2025.1 | ₹1,95,000 | ₹0 | Not covered (§3.4) | Low | Reject |
| CLM-T-4008 | Hospital treatment abroad, no doctor's report | TRV-GLOBE v2025.1 | ₹68,000 | ₹63,000 | Covered | Low (10) | Request info |
| CLM-H-1017 | Hernia repair after the 24-month wait | HLT-SHIELD v2025.1 | ₹81,000 | ₹68,400 | Covered | Low | Partial approval |
| CLM-H-1018 | Severe dengue, ICU above the per-day limit | HLT-SHIELD v2025.1 | ₹94,000 | ₹69,300 | Covered | Low | Partial approval |
| CLM-H-1019 | Road accident 11 days into cover | HLT-SHIELD v2025.1 | ₹80,000 | ₹67,500 | Covered | Low (20) | Partial approval |
| CLM-H-1020 | Known hypertension after the 36-month wait | HLT-SHIELD v2025.1 | ₹48,000 | ₹34,200 | Covered | Low | Partial approval |
| CLM-H-1021 | Admission after the policy lapsed | HLT-SHIELD v2025.1 | ₹27,000 | ₹0 | Not covered (§2.1) | Low | Reject |
| CLM-M-2008 | Car over five years old: 40% on metal | MTR-SECURE v2025.1 | ₹47,000 | ₹30,400 | Covered | Low | Partial approval |
| CLM-M-2009 | Flood in a basement car park | MTR-SECURE v2025.1 | ₹68,000 | ₹48,000 | Covered | Low | Partial approval |
| CLM-M-2010 | New car under six months, 1598cc | MTR-SECURE v2025.1 | ₹69,000 | ₹50,000 | Covered | Low | Partial approval |
| CLM-M-2011 | Malicious damage with a police report | MTR-SECURE v2025.1 | ₹48,000 | ₹38,000 | Covered | Low | Partial approval |
| CLM-P-3009 | Burst water tank pipe | HOME-GUARD v2025.1 | ₹1,39,000 | ₹1,19,200 | Covered | Low | Partial approval |
| CLM-P-3010 | Cyclone, home underinsured | HOME-GUARD v2025.1 | ₹1,45,000 | ₹98,800 | Covered | Low | Partial approval |
| CLM-P-3011 | Earthquake damage to walls and contents | HOME-GUARD v2025.1 | ₹1,68,000 | ₹1,49,000 | Covered | Low | Partial approval |
| CLM-T-4011 | Trip cut short by a death in the family | TRV-GLOBE v2025.1 | ₹92,000 | ₹87,000 | Covered | Low | Partial approval |
| CLM-T-4012 | Heart attack in New York | TRV-GLOBE v2025.1 | ₹8,49,000 | ₹8,40,000 | Covered | Low | Partial approval |
| CLM-T-4013 | Lost baggage inside every limit | TRV-GLOBE v2025.1 | ₹69,000 | ₹64,000 | Covered | Low | Partial approval |
| CLM-T-4014 | Scooter accident in Bali, ambulance | TRV-GLOBE v2025.1 | ₹1,85,500 | ₹1,79,000 | Covered | Low | Partial approval |

CLM-H-1001 waterfall, as the app shows it:

| Rule | Step | Adjustment | Running total | Clause |
|---|---|---:|---:|---|
| R00_GROSS | Itemised charges | ₹1,06,600 | ₹1,06,600 | |
| R20_PER_DAY_LIMIT | Room rent: 3 days × min(6,500, 5,000) | −₹4,500 | ₹1,02,100 | §2.2 |
| R10_NON_PAYABLE | Consumables (gloves, masks, kit) | −₹3,400 | ₹98,700 | §4.3 |
| R30_DEDUCTIBLE | Deductible | −₹5,000 | ₹93,700 | §5.1 |
| R40_COPAY | Co-payment 10% | −₹9,370 | ₹84,330 | §5.2 |
| R50_MAX_LIABILITY | Within sum insured ₹5,00,000 | — | **₹84,330** | §5.3 |

**Synthetic portfolio check.** The same risk rules scored a 1,000-claim synthetic portfolio across all four lines (507 health, 241 motor, 124 property, 128 travel) with 69 injected anomalies: precision 86.6%, recall 84.1% (TP 58, FP 9, FN 11, TN 922). This only shows the rules recover patterns we injected ourselves; it says nothing about real-world fraud detection.

| | |
|---|---|
| ![Claim analysis](docs/screenshots/02-claim-analysis.png) | ![Rejected for waiting period](docs/screenshots/04-claim-rejected-waiting-period.png) |
| ![High-risk claim](docs/screenshots/05-claim-high-risk.png) | ![Motor depreciation](docs/screenshots/06-motor-depreciation.png) |
| ![Policy assistant](docs/screenshots/07-policy-assistant.png) | ![Review queue](docs/screenshots/08-review-queue.png) |
| ![Repudiation letter](docs/screenshots/12-rejection-letter.png) | ![Golden evaluation](docs/screenshots/13-evaluation.png) |
| ![Policy PDF ingestion](docs/screenshots/15-policy-pdf-ingestion.png) | ![Claim evidence tab](docs/screenshots/16-claim-evidence.png) |
| ![Data provenance](docs/screenshots/17-data-provenance.png) | ![Fact correction](docs/screenshots/18-fact-correction.png) |
| ![Home claim with average clause](docs/screenshots/20-property-claim-adjudication.png) | ![Travel baggage limits](docs/screenshots/21-travel-claim-adjudication.png) |
| ![Claims on all four lines](docs/screenshots/22-claims-all-lines.png) | ![Claims filtered from the dashboard](docs/screenshots/24-claims-filtered-travel.png) |

On a phone the navigation collapses into a menu: [screenshot](docs/screenshots/19-mobile-dashboard.png).

The screenshots come from a freshly seeded stack; `node e2e/screenshots.mjs` regenerates them (see [docs/TESTING.md](docs/TESTING.md)).

## Architecture

```mermaid
flowchart TD
    UI[React dashboard] -->|REST /api/v1| API[FastAPI]
    API --> SUP[Supervisor / Claim Orchestrator]
    SUP --> IA[Intake Agent<br/>consolidate facts, find policy]
    IA --> PA[Policy Retrieval Agent<br/>version in force + hybrid RAG]
    PA --> CA[Coverage Agent<br/>period, waiting periods, exclusions, documents]
    CA --> ADJ[Adjudication Tool<br/>deterministic Decimal rules]
    ADJ --> RA[Risk/Fraud Agent<br/>weighted transparent signals]
    RA --> EA[Evidence Agent<br/>evidence package + recommendation]
    EA --> RW[Review/Workflow Agent<br/>route to human queue]
    RW --> AU[Audit Agent]
    API --> DOC[Document Intelligence Agent<br/>PDF/text extraction, classification, facts]
    API --> RAG[Policy knowledge service<br/>BM25 + n-gram vectors, RRF]
    SUP & DOC & RAG --> DB[(PostgreSQL or SQLite)]
```

- One FastAPI modular monolith; agents are bounded modules with explicit tools, and each run persists agent runs, tool calls, timings and a correlation ID.
- The LLM is optional and never computes money or decides claims. Without `ANTHROPIC_API_KEY`, the assistant answers by quoting the wording it retrieved.
- Agent failures stop the run safely and route the claim to `NEEDS_ATTENTION`. Re-running analysis supersedes the previous recommendation and task.

More detail: [product requirements](docs/PRD.md), [architecture](docs/ARCHITECTURE.md), [database](docs/DATABASE.md), [decisions](docs/DECISIONS.md), [design system](docs/DESIGN_SYSTEM.md), [code style](docs/CODE_STYLE.md), [testing](docs/TESTING.md), [agents](docs/AGENTS.md), [release readiness](docs/RELEASE_READINESS.md), [final validation report](docs/FINAL_VALIDATION_REPORT.md) and [release notes](RELEASE_NOTES.md).

## Run it

### Docker (app + PostgreSQL)

```bash
docker compose up --build
# open http://localhost:8080
python3 scripts/smoke_test.py http://localhost:8080   # golden-path smoke test (signs in as supervisor)
```

### Local development

```bash
# backend (Python 3.11+)
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000      # seeds synthetic data on first start

# frontend (Node 20+), in another terminal
cd frontend
npm install
npm run dev                                      # http://localhost:5173, proxies /api to :8000
```

Configuration lives in environment variables; see [.env.example](.env.example). API docs are served at `/docs`.

### Demo accounts

All accounts are synthetic. The password is `DEMO_PASSWORD` (default `claimsense-demo`); set `AUTH_SECRET` to a long random value in any shared deployment.

| Username | Role | Can do |
|---|---|---|
| `adjuster` | Adjuster | Create and analyse claims, decide up to ₹2,00,000, escalate above that |
| `supervisor` | Supervisor | Everything, no limit, decide escalated claims, ingest policy wordings |
| `auditor` | Auditor | Read-only |

### Try the golden path

1. Sign in as `adjuster`, open **New claim**, pick policy `CS-HLT-23-000089` (Fatima Shaikh).
2. Upload the three files in [`data/claims/demo_upload/`](data/claims/demo_upload) and press **Create, upload and analyse**.
3. Review the recommendation on the Overview tab, then the Coverage, Adjudication (₹78,000 billed, ₹64,080 payable), Risk and Policy & evidence tabs.
4. Approve it on the Review tab. The claim, review queue, dashboard and audit trail all update.
5. Press **Generate letter** for the settlement letter (₹64,080.00), or open `CLM-H-1002` for a repudiation letter citing clause 3.3.
6. Before analysing, the Documents tab lists the extracted facts; **Correct** one with a reason and re-run the analysis to use it.
7. Sign in as `supervisor`, open **Policy library** and ingest `data/policies/ingest_demo/HLT-SHIELD_2026.1.pdf` with its `.terms.json`: the 6-page PDF becomes 21 cited clauses of a new 2026.1 version, and the assistant can answer from it.

## Tests and checks

```bash
cd backend && ruff check app tests && python -m pytest -q    # 109 tests
python3 scripts/evaluate.py                                  # golden evaluation -> reports/evaluation.md
python3 scripts/claims_report.py                             # every claim packet -> reports/claims_results.md
python3 scripts/provenance.py --check                        # source registry, checksums, RAG manifest
cd frontend && npm run build                                 # type check + production build
cd e2e && npm ci && npx playwright test                      # 12 browser tests against a fresh stack on :8080
```

Tests cover sign-in, roles, approval limits and escalation, security headers and upload path handling, the rules engine (hand-calculated waterfalls, rounding, caps, depreciation bands), the clause parser and retriever, extraction from text and PDF, risk levels, all 19 golden scenarios, the property and travel rules (average clause, per-item and benefit limits, trip period, loss-dependent documents), settlement-clock states, letter content for each decision type, CSV export, the full create → upload → analyse → review API flow, safe failure, upload validation and policy-ingestion validation. CI runs these plus the golden evaluation ([reports/evaluation.md](reports/evaluation.md), 449 / 449 checks), the provenance check, `pip-audit`, `npm audit`, and on a Docker + PostgreSQL stack the Playwright browser suite and the smoke test ([.github/workflows/ci.yml](.github/workflows/ci.yml)). Results: [docs/FINAL_VALIDATION_REPORT.md](docs/FINAL_VALIDATION_REPORT.md). Security controls and known gaps: [docs/SECURITY.md](docs/SECURITY.md).

## Data and datasets

| Data | Status |
|---|---|
| Synthetic policy wordings: HLT-SHIELD 2024.1 and 2025.1, MTR-SECURE 2025.1, HOME-GUARD 2025.1, TRV-GLOBE 2025.1, each with structured terms that cite clauses | In use |
| 50 synthetic golden claim packets across the four lines (claim forms, bills, estimates, discharge summaries, police reports, surveyor loss assessments, travel expense statements, airline irregularity reports; one as PDF) | In use |
| 1,000-claim synthetic portfolio across the four lines with labelled injected anomaly patterns | In use for analytics and rule evaluation |
| IRDAI 2024 master circulars and statistics handbook, APRA NCPD 2026, CMS TiC PUF PY2026, Figshare 2025 and Zenodo 2024 claims datasets | Registered with publication date, URL, licence status and intended use; not downloaded in this build |

Everything is regenerated deterministically with `python data/synthetic/generate.py`; then `python scripts/provenance.py --write` re-stamps the checksums in [data/source_registry.json](data/source_registry.json). The wording borrows common Indian retail-insurance concepts but is not any insurer's product and not regulatory text. Never commit real customer data or confidential policy documents.

## Deployment

- **Docker**: one image serves the UI and the API (`Dockerfile`); `docker-compose.yml` adds PostgreSQL.
- **Azure Container Apps**: manual workflow [.github/workflows/deploy-azure.yml](.github/workflows/deploy-azure.yml) builds, deploys and runs the smoke test. Needs Azure credentials in repository secrets.
- **Render**: [render.yaml](render.yaml) blueprint for a one-click demo deployment. After merging to `main`, use the button below, or on render.com choose New → Blueprint and pick this repository. Set `DEMO_PASSWORD` when asked.

  [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/sricharansk/CLAIM-SENSE)

**Deployed** on Render at https://claim-sense.onrender.com from `main`; verified 2026-10-12 ([Verify deployment run](https://github.com/sricharansk/CLAIM-SENSE/actions/runs/38266390199)). After each deploy, run `python3 scripts/smoke_test.py https://<service> <DEMO_PASSWORD>` (or the **Verify deployment** workflow in GitHub Actions) before calling it live. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Repository layout

```text
backend/app/
  agents/        supervisor + intake, document, policy, coverage, adjudicator, risk, evidence, review, audit
  adjudication/  deterministic rules engine
  rag/           clause parser, hybrid retriever, grounded answers
  api/routes.py  REST API v1
backend/tests/   pytest suite
frontend/src/    React + TypeScript UI (pages/, components/, api.ts)
data/            synthetic policies, claim packets, portfolio, source registry, generator
docs/            blueprint, status, architecture, decisions, deployment, validation report, screenshots, presentation
e2e/             Playwright browser tests (run against a running stack)
reports/         golden evaluation, results on every claim packet, RAG ingestion manifest
references/      supporting planning documents
scripts/         smoke_test.py, evaluate.py, claims_report.py, provenance.py
```

## Project presentation

The M.Tech Review III presentation (16 slides: introduction, objectives, modules, problem statement, architecture and workflow diagrams, approach, results, conclusion and references) is at [docs/presentation/Claim_Sense_Review_III_SK_Sricharan.pptx](docs/presentation/Claim_Sense_Review_III_SK_Sricharan.pptx). Its figures come from `reports/claims_results.md` and `reports/evaluation.md`.

## Roadmap

Single sign-on (Azure AD / OIDC) and user management, OCR for scanned images, embedding retriever as a third ranker, ingestion of the registered IRDAI circulars into the RAG corpus, ML fraud model on the Figshare dataset, more property perils and travel benefits (third-party liability, trip delay), background job queue, Azure AI Search, Key Vault and Application Insights. Status and next actions: [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).

## Disclaimer

Claim Sense is decision support. Recommendations always require a human decision, and outputs from this demo must not be used for real claims.
