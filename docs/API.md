# API

REST contract for the Claim Sense backend. Routes are defined in `backend/app/api/routes.py` on two routers, both prefixed `/api/v1`: `public` (no sign-in) and `router` (every route requires a signed-in user). Error handling is in `backend/app/main.py`. FastAPI also serves its generated OpenAPI schema at `/openapi.json` and interactive docs at `/docs` and `/redoc`.

## Conventions

- **Auth.** `Authorization: Bearer <token>`, token from `POST /api/v1/auth/login`. Tokens are HMAC-SHA256 signed and expire after `TOKEN_TTL_HOURS` (default 12, `backend/app/auth.py`).
- **Roles.** The table's *Access* column uses these levels, enforced by dependencies in `backend/app/auth.py`:
  - *Public*: no token needed.
  - *Signed in*: any of ADJUSTER, SUPERVISOR, AUDITOR (`current_user`).
  - *Writer*: ADJUSTER or SUPERVISOR (`writer`); an auditor gets 403 `Your role is read-only`.
  - *Supervisor*: SUPERVISOR only (`supervisor`); others get 403 `Only a supervisor can do this`.
- **Money** is returned as a string with two decimals (`_money` in `routes.py`), for example `"64080.00"`.
- **Dates** are ISO 8601 (`YYYY-MM-DD`); timestamps are ISO 8601 with time zone.
- **Claim numbers** are the public identifier in paths (`CLM-H-1001`). New claims get `<prefix>-<3000 + n>`, where n is the claim count plus one and the prefix comes from `CLAIM_PREFIX` in `routes.py` (`CLM-H` health, `CLM-M` motor, `CLM-P` property, `CLM-T` travel, `CLM-A` personal accident, `CLM-L` life).
- **Lines of business** (`claim_type`) must match `^(health|motor|property|travel|personal_accident|life)$` (`ClaimIn` in `routes.py`).
- **Correlation ID.** Every response carries an `x-correlation-id` header. A client may send its own `x-correlation-id`; otherwise the server generates `req-<12 hex>` (`main.py`).

## Error response

Errors raised as `HTTPException`, validation errors and unhandled exceptions share one shape (`main.py`):

```json
{"error": {"code": "HTTP_404", "message": "Claim CLM-X-1 not found", "correlation_id": "req-3f2a9c1b7d4e"}}
```

| Code | Status | Raised by |
|---|---|---|
| `HTTP_<status>` | 401, 403, 404, 409, 422, 429 | `HTTPException` in a handler or auth dependency; headers such as `Retry-After` are passed through |
| `VALIDATION_ERROR` | 422 | Request body or query fails the Pydantic model; `message` joins `field: reason` pairs with `; ` |
| `INTERNAL_ERROR` | 500 | Any other exception; message is `Unexpected server error. Quote the correlation ID when reporting it.` No stack trace is returned; it is logged with the correlation ID |

Exception: a path or method that matches no route returns FastAPI's default body, `{"detail": "Not Found"}` (404) or `{"detail": "Method Not Allowed"}` (405), because only `fastapi.HTTPException` has a custom handler. In the Docker image, which mounts the built UI, an unmatched **GET** is answered by the SPA catch-all in `main.py` with `index.html` and status 200, including unmatched paths under `/api/v1`.

## Endpoints

### Health and sign-in

| Method | Path | Access | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/api/v1/health` | Public | – | `status: "ok"`, `service`, `version` | – |
| GET | `/api/v1/ready` | Public | – | `status: "ready"`, `database: "ok"`, `policy_index: "ok" \| "empty"`, `llm: "anthropic" \| "disabled (extractive answers)"`, `database_backend` (`sqlite` or `postgresql`) | 500 if the database query fails |
| POST | `/api/v1/auth/login` | Public | `LoginIn`: `username` (1–60), `password` (1–200). Username is trimmed and lower-cased | `token`, `user` (see `/auth/me`) | 401 `Wrong username or password`; 429 `Too many failed sign-ins. Try again in N seconds.` with `Retry-After`; 422 |
| GET | `/api/v1/auth/me` | Signed in | – | `username`, `display_name`, `role`, `approval_limit` (string or null), `can_write`, `is_supervisor` | 401 |

### Claims

| Method | Path | Access | Request | Response | Errors |
|---|---|---|---|---|---|
| POST | `/api/v1/claims` | Writer | `ClaimIn`: `policy_number` (3–40), `claim_type` (line pattern), `claimant_name` (2–200), `incident_date` (date, optional), `claimed_amount` (decimal ≥ 0, optional), `description` (≤ 4000, default "") | 201, claim summary (below) | 422 `Policy number … is not in the policy register`; 403; 422 validation |
| GET | `/api/v1/claims` | Signed in | Query, both optional: `status` (one status), `q` (claim, claimant or policy number, case-insensitive substring). The Claims screen filters by line, risk and recommendation in the browser | Array of claim summaries, newest first | – |
| GET | `/api/v1/claims-export.csv` | Signed in | – | `text/csv` attachment `claim-sense-claims.csv`, columns `claim_number, claim_type, policy_number, claimant_name, incident_date, claimed_amount, recommendation, recommended_payable, risk_level, status, settlement_due, settlement_state, created_at` | – |
| GET | `/api/v1/claims/{claim_number}` | Signed in | – | Claim summary plus `description`, `documents[]` (`id, filename, doc_type, pages, status, uploaded_at`), `fact_view[]`, `facts[]`, `analysis` (as `GET …/analysis`, or null), `decisions[]` (`id, source AI\|HUMAN, decision, payable_amount, actor, notes, created_at`), `workflow_task` (`id, queue, priority, status, assignee, created_at` or null), `audit[]` | 404 |
| POST | `/api/v1/claims/{claim_number}/documents` | Writer | `multipart/form-data`, one or more `files` parts (`.pdf`, `.txt`, `.md`) | 201, array of `id, filename, doc_type, pages, facts_extracted` | 404; 409 `Claim is closed; documents can no longer be added`; 422 unsupported type, larger than `MAX_UPLOAD_BYTES`, empty, or unreadable. One bad file fails the whole request |
| GET | `/api/v1/claims/{claim_number}/documents/{doc_id}` | Signed in | – | `id, filename, doc_type, pages, text` | 404 claim; 404 `Document not found` |
| POST | `/api/v1/claims/{claim_number}/facts` | Writer | `FactCorrectionIn`: `name`, `value` (1–500), `reason` (≤ 1000, must not be blank) | 201, `id, name, value, previous` | 404; 409 `Claim already approved\|rejected`; 422 fact not correctable (every extracted single-value fact except `document_total`, see `CORRECTABLE` in `agents/intake.py`); 422 `Give a reason for the correction`; 422 when a date is not `YYYY-MM-DD` or `claimed_amount` is not a non-negative number |
| POST | `/api/v1/claims/{claim_number}/analyze` | Writer | – | Analysis object (below). A run that an agent stops safely still returns 200 with `status: "FAILED"` and `error` | 404; 409 `Claim already decided; reopen is not supported in this version` |
| GET | `/api/v1/claims/{claim_number}/analysis` | Signed in | – | Latest analysis object | 404 claim; 404 `Claim has not been analysed yet` |
| GET | `/api/v1/claims/{claim_number}/letter` | Signed in | – | `claim_number, kind` (`SETTLEMENT`, `REPUDIATION`, `DOCUMENT_REQUEST`, `UNDER_REVIEW`), `status` (`FINAL` or `DRAFT`), `date, to{name, policy_number, holder}, from, subject, paragraphs[], references[], signed_by, based_on` (`backend/app/letters.py`) | 404; 409 `Run the analysis before generating a letter` |
| POST | `/api/v1/claims/{claim_number}/review` | Writer | `ReviewIn`: `action` (`APPROVE`, `REJECT`, `REQUEST_INFO`, `INVESTIGATE`, `ESCALATE`), `notes` (≤ 4000), `payable_amount` (decimal ≥ 0, optional, used for `APPROVE`; defaults to the AI payable) | `claim_number, status, decision, payable_amount` | See *Review rules* below |

**Claim summary** fields (`_claim_summary`): `claim_number, policy_number, claim_type, claimant_name, incident_date, claimed_amount, status, created_at, updated_at, recommendation, recommended_payable, risk_level, documents` (count), `settlement` (`start, due_date, days, clause, days_left, state, decided_on`; `state` is `ON_TRACK`, `DUE_SOON`, `OVERDUE`, `MET` or `BREACHED`, from `backend/app/sla.py`). The create response has `settlement: null`.

**Analysis object** (`_analysis`): `run_id, correlation_id, status` (`SUCCEEDED` or `FAILED`), `error, started_at, finished_at, rules_version, agents[]` (`agent, status, summary, tool_calls[{tool, args, result, ms}], duration_ms`), `result`. On success `result` holds `claim_number, correlation_id, policy, facts, fact_sources, line_items, coverage, adjudication, risk, evidence, retrieval, recommendation` (`backend/app/agents/supervisor.py`); on failure it is null.

**Review rules** (`review_claim`, checked in this order):

| Status | Condition |
|---|---|
| 404 | Claim not found |
| 422 | `action` is not one of the five actions |
| 409 | Claim already approved or rejected |
| 409 | `Run the AI analysis before recording a decision` (no AI recommendation yet) |
| 422 | `REJECT`, `ESCALATE` or `INVESTIGATE` without notes |
| 403 | Claim is `ESCALATED` and the user is not a supervisor |
| 409 | The open task is assigned to someone else and the user is not a supervisor |
| 403 | `APPROVE` amount is above the user's approval limit (adjuster: ₹2,00,000, `DEMO_USERS` in `auth.py`) |

### Review queue

| Method | Path | Access | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/api/v1/reviews` | Signed in | – | Open tasks sorted by priority (HIGH, MEDIUM, NORMAL) then age: `task_id, queue, priority, assignee, created_at, age_hours, claim_number, claimant_name, claim_type, claimed_amount, status, risk_level, recommendation, recommended_payable, settlement` | – |
| GET | `/api/v1/reviewers` | Signed in | – | Active adjusters and supervisors: `username, display_name, role` | – |
| POST | `/api/v1/reviews/{task_id}/assign` | Writer | `AssignIn`: `username` (≤ 60) or null to release | `task_id, claim_number, queue, assignee` | 404 task; 409 task not open; 422 `<username> is not a reviewer`; for non-supervisors: 403 assigning to someone else, 403 taking a `SUPERVISOR_REVIEW` task, 409 task assigned to someone else |

Queues and priorities come from `backend/app/agents/review.py`: `SIU_INVESTIGATION` (HIGH), `PENDING_INFORMATION` (MEDIUM), `ADJUSTER_REVIEW` (MEDIUM for recommended rejection, NORMAL otherwise) and `SUPERVISOR_REVIEW` (HIGH, after an escalation).

### Policies and policy assistant

| Method | Path | Access | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/api/v1/policies` | Signed in | – | `product_code, name, line_of_business, insurer, synthetic, versions[]` (`id, version, effective_from, effective_to, clauses` count, `source_file`) | – |
| POST | `/api/v1/policies` | Supervisor | `multipart/form-data`: `wording` (`.pdf`, `.md` or `.txt`) and `terms` (JSON object) | 201, `product_code, version, clauses, ingestion` (ingestion record, below) | 422 `Structured terms are not valid JSON: …`; 422 `Ingestion #N failed: <reason>` (the FAILED record is kept); 403 |
| GET | `/api/v1/policy-ingestions` | Signed in | – | Latest 50 ingestion records: `id, filename, file_type, sha256, size_bytes, status, stages[{status, at, detail}], product_code, version, pages, clauses, warnings[], error, actor, created_at, finished_at` | – |
| GET | `/api/v1/policies/{product_code}` | Signed in | – | One entry of `GET /policies` | 404 `Policy … not found` |
| GET | `/api/v1/policies/{product_code}/versions` | Signed in | – | `id, version, effective_from, effective_to, terms, clauses[{id, clause_ref, title, section, page, text}]` | 404 |
| GET | `/api/v1/insured-policies` | Signed in | – | `policy_number, product_code, line_of_business, holder_name, start_date, end_date, sum_insured` | – |
| POST | `/api/v1/rag/query` | Signed in | `RagQuery`: `question` (3–1000), `product_code` (optional), `version` (optional) | `question, grounded, mode` (`extractive`, `llm` or `refusal`), `answer, citations[]` (`clause_id, clause_ref, title, section, page, policy, product_code, version, document, text, score, bm25, cosine, bm25_rank, vector_rank`) | 404 unknown product; 404 `Version … not found for …`; 422 |

Ingestion failure reasons (`ingest_policy_file` in `backend/app/services.py`): unsupported type, empty file, larger than `MAX_UPLOAD_BYTES`, identical file already READY (same SHA-256), missing required terms, bad or reversed effective dates, version already exists, unreadable PDF, PDF without a text layer, non-UTF-8 text, no clauses found, terms citing clauses that are not in the wording.

### Audit, analytics and reference data

| Method | Path | Access | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/api/v1/audit` | Signed in | Query: `claim_number` (optional), `limit` (default 100, max 500) | Newest first: `id, claim_number, event_type, actor, details, correlation_id, created_at` | 404 unknown claim; 422 `limit` over 500 |
| GET | `/api/v1/analytics` | Signed in | – | `lines` (claims, claimed and payable per line), `totals, by_status, by_recommendation, by_risk, by_line, queues, settlement, human_vs_ai, human_outcomes, portfolio` (`backend/app/analytics.py`). `portfolio` scores the 10,000-claim `data/synthetic/claims_portfolio.csv` with the live risk rules and is null when the file is missing | – |
| GET | `/api/v1/benchmarks/industry` | Signed in | – | Aggregated CAS Schedule P industry loss-reserving benchmarks, read from `data/public/cas_schedule_p/benchmark.json` (written by `scripts/fetch_public_data.py`): `dataset_id, source` (`name, publisher, url, retrieved_from, archive_sha256, file, file_sha256, retrieval_date, units, transformation_script`), `definitions, rows_read, lines` (per Schedule P line: `label, companies, net_earned_premium, incurred_at_10_years, loss_ratio, paid_development[{lag_years, percent_paid}], accident_years[]`), `note`, and `registry` (the `cas-schedule-p-1998-2007` entry from the validated source registry, or null) | 404 `Industry benchmark not generated; run scripts/fetch_public_data.py` |
| GET | `/api/v1/evaluation` | Signed in | – | Committed golden evaluation report `reports/evaluation.json` | 404 `No evaluation report yet. Run python scripts/evaluate.py.` |
| GET | `/api/v1/datasets` | Signed in | – | Source registry validated on request: `schema_version, sources[], problems[], valid` (`backend/app/provenance.py`) | – |
| GET | `/api/v1/knowledge-base/manifest` | Signed in | – | RAG manifest: `manifest_version, indexed_chunks, rejected_chunks, documents[], chunks[], rejected[]` | – |

Every signed-in route also returns 401 `Sign in to continue` when the token is missing, invalid, expired, or names an inactive user.

## Side effects worth knowing

| Call | Writes |
|---|---|
| `POST /auth/login` | `LOGIN`, `LOGIN_FAILED` or `LOGIN_THROTTLED` audit event |
| `POST /claims` | Claim row, `CLAIM_CREATED` |
| `POST /claims/{n}/documents` | Stored file under `CLAIMSENSE_STORAGE_DIR/<claim>/`, document and fact rows, `DOCUMENT_UPLOADED`; sets the claim's incident date and amount if they were empty |
| `POST /claims/{n}/facts` | Correction fact (the extracted one is kept), `FACT_CORRECTED` |
| `POST /claims/{n}/analyze` | `analysis_runs`, `agent_runs`, AI `claim_decisions`, a new workflow task (open tasks are superseded), stage audit events under the run's correlation ID |
| `POST /claims/{n}/review` | HUMAN `claim_decisions`, claim status, task queue/assignee/status, `HUMAN_DECISION` |
| `POST /reviews/{id}/assign` | Task assignee, `TASK_ASSIGNED` or `TASK_RELEASED` |
| `POST /policies` | Ingestion record, policy version and clauses, `POLICY_INGESTED` or `POLICY_INGESTION_FAILED`; rebuilds the retrieval index on success |
| `POST /rag/query` | `RAG_QUERY` audit event with the question and cited clause IDs |
