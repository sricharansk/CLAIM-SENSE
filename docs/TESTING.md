# Testing and validation — Claim Sense

## Commands

```bash
cd backend && ruff check app tests ../scripts && python -m pytest -q     # 222 tests
python3 scripts/evaluate.py                                             # golden evaluation, 365 checks
python3 scripts/provenance.py --check                                   # registry, checksums, reproducible RAG manifest
cd frontend && npm run build                                            # type check + build
cd e2e && npx playwright test                                           # 13 browser tests (fresh stack)
docker compose up --build -d && python3 scripts/smoke_test.py http://localhost:8080
```

CI (`.github/workflows/ci.yml`) runs all of these on every push and pull request. It also runs `pip-audit` and `npm audit`.

## Unit and API tests (`backend/tests/`)

| File | Tests | Covers |
|---|---|---|
| `test_adjudication.py` | 7 | Hand-calculated waterfalls, rounding, caps, depreciation bands |
| `test_rag.py` | 5 | Clause parser keeps page/section/clause; hybrid ranking; cited answers; synonyms; refusal |
| `test_extraction.py` | 4 | Field and line-item extraction from text and PDF |
| `test_golden_path.py` | 19 | All eight seeded scenarios; version matching; rejection citation; duplicates; create → upload → analyse → review; safe failure; validation; headers and error shape |
| `test_auth.py` | 7 | Sign-in, roles, approval limit, escalation, read-only auditor |
| `test_letters_sla.py` | 7 | Settlement-clock states; letter content per decision type; CSV export |
| `test_evaluation.py` | 3 | Evaluation report served and complete; sign-in required; refusals |
| `test_security_guards.py` | 4 | Sign-in throttle; injection scan; injected document flagged with amount unchanged; override and escalation rates |
| `test_policy_ingestion.py` | 4 | PDF ingestion with pages and states; duplicate, scanned, unreadable and wrong-type failures; supervisor only; seeded records |
| `test_fact_correction.py` | 2 | Correction used by the next analysis, audited, extracted value kept, latest wins; date, amount, reason, role and decided-claim validation |
| `test_provenance.py` | 6 | Committed registry valid; validator rejects missing or wrong provenance and checksum drift; `/datasets`; every indexed chunk resolves; a chunk without an extraction run is kept out of the index; backfill |
| `test_demo_book.py` | 133 | Each of the 77 demo-book claims (all six lines) reaches its designed recommendation; replayed reviewer history (status, labelled notes, display-name actors, review rules, backdated timestamps, audit events); dashboard line and period filters and panels; claims-list drill-down filters; sample packet endpoints |
| `test_more_lines.py` | 18 | Travel, home, personal accident and life rules worked by hand (depreciation, per-item and category limits, average clause on the full sum insured, benefit schedule rows); claim type must match the policy's line; each line's sample packet through the pipeline; industry benchmark endpoint; 10,000-claim portfolio |
| `test_review_assignment.py` | 3 | Queue shows risk, age and assignee; take, release and supervisor reassignment; others cannot take or decide an assigned task; supervisor-queue and auditor limits; audit events |

Tests use an isolated temporary SQLite database seeded from `data/`. The LLM is always off.

## Golden evaluation (`scripts/evaluate.py`)

- **Claim cases:** 16, covering all ten blueprint case types: clearly covered, excluded, partial, insufficient evidence, high risk, deductible, sub-limit, maximum coverage, duplicate, and ambiguous policy version. C13 to C16 are travel (baggage depreciation, per-item and trip-delay limits), home (jewellery limit and the average clause), personal accident (benefit schedule pays above the amount claimed) and life (suicide exclusion in the first 12 months).
- **Policy questions:** 30, split into covered, excluded, ambiguous and unsupported; Q22 to Q30 ask about the travel, home, personal accident and life wordings.
- **Expected values:** worked out by hand in `data/evaluation/golden_cases.json`.
- **Scoring:** results are scored on retrieval, citations, groundedness, coverage, amounts, risk and workflow. The report is written to `reports/evaluation.{json,md}` and shown at `/evaluation`. CI fails on any failed check.

## End-to-end

- **`scripts/smoke_test.py <url> [password]`:** checks the frontend, health and readiness, sign-in enforcement, seeded data, policy ingestion records, the evaluation report, the source registry and the RAG manifest. It then runs the golden claim: create, upload, analyse, coverage, adjudication (₹64,080), citations, human review, audit, assistant answer and refusal.
- **Browser runs (Playwright, Chromium) against the Docker image:**
  - sign in;
  - create a claim, upload, analyse;
  - see the approval-limit block;
  - approve and generate letters;
  - export CSV;
  - assistant;
  - evaluation screen;
  - escalate;
  - see the dashboard rates;
  - PDF policy ingestion;
  - take, release and reassign review tasks.

  The screenshots are in `docs/screenshots/`.

## Browser tests (`e2e/`)

`e2e/tests/golden.spec.mjs` has 13 Playwright tests that drive the real UI against a running stack (`BASE_URL`, default `http://localhost:8080`):

- golden claim to approval and letter, with the stage audit events;
- approval-limit block;
- cited rejection;
- assistant answer and refusal;
- evaluation scorecard;
- take and release a review task;
- fact correction and re-run;
- data provenance;
- dashboard rates;
- dashboard filters and tiles drilling down to the matching claims, and the guide's links;
- the travel sample packet run through the pipeline (₹35,800 with the baggage and trip-delay limits);
- the industry benchmark and the 10,000-claim portfolio on screen;
- phone layout (dashboard, claims, two claims, review queue, guide, new claim, data sources).

Any browser console error fails a test. They need a freshly seeded stack, because a second run files the golden claim again and the system flags it as a duplicate. CI runs them in the `docker-smoke` job before the smoke test.

```bash
docker compose down -v && docker compose up --build -d
cd e2e && npm ci && npx playwright install chromium && npx playwright test
```
