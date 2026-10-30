# Observability

What Claim Sense records about itself, where to look, and what is not built yet. Most of the evidence a reviewer or operator needs lives in the database (audit events, analysis runs, agent runs) and is exposed through the API and UI, not through a monitoring backend.

## Logs

| Item | Detail | Source |
|---|---|---|
| Configuration | `logging.basicConfig(level=INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")`, set when the app module is imported | `backend/app/main.py` |
| Output | Plain text to the process's standard streams. The image sets `PYTHONUNBUFFERED=1`. Read with `docker compose logs app` or the platform's log view | `Dockerfile` |
| HTTP access log | Uvicorn's own default access and error logs (the app does not configure them) | `Dockerfile` `CMD` |
| Format | Not JSON; no request fields beyond what the message includes | – |

Application loggers and what they write:

| Logger | Level | Message | Source |
|---|---|---|---|
| `claimsense` | ERROR (with traceback) | `unhandled error [<correlation id>]` for every 500 | `main.py` |
| `claimsense.auth` | WARNING | `AUTH_SECRET not set: using a random per-process signing key` | `auth.py` |
| `claimsense.llm` | WARNING | `LLM call failed, using extractive answer: <reason>` | `llm.py` |
| `claimsense.rag` | WARNING | `<n> clause chunks kept out of the index for missing provenance: …` | `rag/service.py` |
| `claimsense.seed` | WARNING / INFO | `source registry: <problem>`; `seed complete: {...}` | `seed.py` |

Business events (sign-in, claim, analysis, decisions) are not logged; they are audit events in the database (below).

## Correlation IDs

There are two kinds, generated in different places.

| ID | Format | Created | Where it appears |
|---|---|---|---|
| Request | `req-<12 hex>`, or the caller's `x-correlation-id` header if sent | `correlation_id` middleware, `main.py` | `x-correlation-id` response header on every response; `error.correlation_id` in error bodies; the unhandled-error log line; the UI's error box |
| Analysis run | `cs-<12 hex>` | `analyze_claim`, `agents/supervisor.py` | `analysis_runs.correlation_id`; `correlation_id` in the analysis response and its `result`; every pipeline audit event; the claim's agent pipeline card |

The request ID is not stored in the database. Audit events outside the analysis pipeline (sign-in, claim creation, uploads, fact corrections, assignments, human decisions, policy ingestion, assistant queries) are written with a null `correlation_id`, so they are linked by claim and actor rather than by ID.

## Audit events

`audit_events` is append-only (`backend/app/agents/audit.py` only inserts). Each row has `claim_id` (nullable), `event_type`, `actor`, `details` (JSON), `correlation_id` and `created_at`. Read them through `GET /api/v1/audit`, the claim detail response, the Audit trail screen and each claim's Audit tab.

| Event | Written by | Correlation ID |
|---|---|---|
| `LOGIN`, `LOGIN_FAILED`, `LOGIN_THROTTLED` | `routes.login` | – |
| `CLAIM_CREATED` | `routes.create_claim` | – |
| `DOCUMENT_UPLOADED` | `services.add_document` | – |
| `FACT_CORRECTED` | `routes.correct_fact` | – |
| `ANALYSIS_STARTED` | `supervisor.analyze_claim` | run |
| `FACTS_EXTRACTED`, `POLICY_SELECTED`, `EVIDENCE_RETRIEVED`, `COVERAGE_ANALYZED`, `ADJUDICATION_CALCULATED`, `RISK_SCORED`, `EVIDENCE_PACKAGED` | `supervisor._stage_events`, actor is the agent name | run |
| `AI_RECOMMENDATION` | `supervisor.analyze_claim` | run |
| `ANALYSIS_FAILED` | `supervisor.analyze_claim` | run |
| `TASK_ASSIGNED`, `TASK_RELEASED` | `routes.assign_task` | – |
| `HUMAN_DECISION` (with `override` and `final` flags) | `review.apply_review` | – |
| `POLICY_INGESTED`, `POLICY_INGESTION_FAILED` | `services.py` | – |
| `RAG_QUERY` (question, grounded, cited clause IDs) | `routes.rag_query` | – |

Actors are usernames, except `HUMAN_DECISION`, whose actor is the reviewer's display name (`apply_review` is passed `user.display_name`), and system actors such as `seed`, `supervisor` and `claim-sense-supervisor`.

## Agent runs and tool calls

Every analysis writes one `analysis_runs` row (`status`, `error`, `rules_version`, `started_at`, `finished_at`, full `result` JSON) and one `agent_runs` row per agent: `agent`, `status`, `summary`, `tool_calls`, `duration_ms`, `started_at` (`backend/app/models.py`).

Tool calls are recorded by `ToolLog.record` (`backend/app/agents/base.py`) as `{"tool", "args", "result", "ms"}`. A failed agent keeps the calls it made before failing. The Review/Workflow and Audit agents are recorded by the supervisor directly. These rows are returned in `analysis.agents` by `GET /claims/{n}` and `GET /claims/{n}/analysis` and shown on the claim Overview's agent pipeline card with each duration and the expandable tool calls.

## Health and readiness

| Endpoint | Checks | Used by |
|---|---|---|
| `GET /api/v1/health` | Nothing beyond the process answering; returns `status`, `service`, `version` | Docker `HEALTHCHECK` (every 15 s, `Dockerfile`); Render `healthCheckPath` (`render.yaml`) |
| `GET /api/v1/ready` | Runs `SELECT 1`; retrieves one clause for "deductible" to confirm the policy index has content; reports whether the LLM is enabled and the database dialect | CI and deploy workflows (wait loops), `scripts/smoke_test.py` (requires `policy_index: "ok"`), the UI sidebar status line |

Both are public. `/ready` returns 500 if the database query fails and 200 with `policy_index: "empty"` if the index is empty; it does not check storage, the LLM provider or the source registry.

## Product metrics in the app

The dashboard (`GET /api/v1/analytics`, `backend/app/analytics.py`) computes these on each request from the database: average analysis time (`finished_at` minus `started_at` of `analysis_runs`), override rate, escalation rate, settlement overdue counts and queue sizes. They describe claims work, not service health, and are not exported anywhere.

## Quality signals

| Signal | What it shows | Where |
|---|---|---|
| Golden evaluation | Claim cases and assistant questions against hand-worked expectations; retrieval hit@1, MRR, refusal accuracy | `scripts/evaluate.py` → `reports/evaluation.{json,md}`, `GET /evaluation`, Evaluation screen |
| Provenance check | Source registry valid, checksums match, RAG manifest reproducible, rejected chunks | `scripts/provenance.py --check`, `GET /datasets`, `GET /knowledge-base/manifest`, Data sources screen |

## Smoke test

`scripts/smoke_test.py <base-url> [password]` uses only the standard library, prints `[PASS]`/`[FAIL]` per check and exits non-zero on the first failure. Checks, in order: served frontend HTML, CSS and JavaScript; `/health`; `/ready` with a non-empty index; 401 without a token; supervisor sign-in; seeded claims present; at least 3 READY policy ingestions; evaluation report all passed; registry valid; manifest with no rejected chunks; create a health claim, upload the three demo documents and check their types; analysis with 8 agent runs, coverage `COVERED`, payable `64080.00`, recommendation `PARTIAL_APPROVAL` (or `INVESTIGATE` when an earlier smoke claim makes it a duplicate) and cited evidence; approve; audit events present; one property, travel, personal accident and life claim filed from the seeded packets, each with its hand-calculated payable; an assistant answer citing clause 2.2; an assistant refusal. Each run adds five claims.

## CI and deployment workflows

| Workflow | Trigger | Steps |
|---|---|---|
| `ci.yml` | Push to `main`, every pull request | **backend**: ruff, pytest, golden evaluation (artifact `evaluation-report`), provenance check, pip-audit. **frontend**: `npm ci`, `npm audit --audit-level=high`, build. **docker-smoke** (after both): Compose stack with PostgreSQL, wait for `/ready` (prints `docker compose logs app` on timeout), Playwright suite (artifact `playwright-report` on failure), smoke test, tear down |
| `deploy-azure.yml` | Manual | Build and deploy to Azure Container Apps, wait for `/ready`, smoke test |
| `verify-deployment.yml` | Manual, with `url` and `browser_tests` inputs | Wait for `/ready`, optional Playwright suite, read-only snapshot of the live claims (`scripts/claims_report.py --live`, artifact `live-claims` and printed in the log), smoke test against the URL |

## Not implemented

Stated plainly, so nobody assumes otherwise:

- No metrics backend: no Prometheus endpoint, no OpenTelemetry, no StatsD.
- No Azure Monitor or Application Insights, and no other APM or tracing.
- No structured (JSON) logs and no log shipping or retention beyond what the host keeps.
- No alerting or uptime monitoring.
- The request correlation ID is not stored with audit events or analysis runs, and is not passed to the LLM call.
- No dashboard of service health; the in-app dashboard covers claims work only.
