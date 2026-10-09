# Testing and validation — Claim Sense

## Commands

```bash
cd backend && ruff check app tests ../scripts && python -m pytest -q     # 71 tests
python3 scripts/evaluate.py                                             # golden evaluation, 256 checks
python3 scripts/provenance.py --check                                   # registry, checksums, reproducible RAG manifest
cd frontend && npm run build                                            # type check + build
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
| `test_review_assignment.py` | 3 | Queue shows risk, age and assignee; take, release and supervisor reassignment; others cannot take or decide an assigned task; supervisor-queue and auditor limits; audit events |

Tests use an isolated temporary SQLite database seeded from `data/`. The LLM is always off.

## Golden evaluation (`scripts/evaluate.py`)

- **Claim cases:** 12, covering all ten blueprint case types: clearly covered, excluded, partial, insufficient evidence, high risk, deductible, sub-limit, maximum coverage, duplicate, and ambiguous policy version.
- **Policy questions:** 21, split into covered, excluded, ambiguous and unsupported.
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

  The scripts are not in the repository; their screenshots are in `docs/screenshots/`.
