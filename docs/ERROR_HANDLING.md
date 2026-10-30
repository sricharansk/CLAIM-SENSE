# Error handling

How Claim Sense fails, what it records when it does, and what the user sees. The principle is the blueprint's: when the system cannot proceed safely it stops, says why, and leaves the decision with a person.

## API errors

All errors share one body (`backend/app/main.py`):

```json
{"error": {"code": "HTTP_409", "message": "Claim already approved", "correlation_id": "req-3f2a9c1b7d4e"}}
```

- `HTTPException` becomes `HTTP_<status>` with the handler's message and any headers (for example `Retry-After`).
- `RequestValidationError` becomes 422 `VALIDATION_ERROR`; the message lists `field: reason` pairs.
- Any other exception becomes 500 `INTERNAL_ERROR` with a fixed message. The stack trace is logged with the correlation ID (`log.exception` on logger `claimsense`) and never sent to the client.
- Unmatched paths and methods are the exception: FastAPI's default `{"detail": "Not Found"}` / `{"detail": "Method Not Allowed"}`. In the Docker image an unmatched GET returns the UI's `index.html` (SPA catch-all).

### Status codes by cause

| Status | Cause | Source |
|---|---|---|
| 401 | No token, bad signature, expired token, inactive user: `Sign in to continue`. Wrong credentials at login: `Wrong username or password` | `auth.current_user`, `routes.login` |
| 403 | Auditor calls a write route (`Your role is read-only`); non-supervisor ingests a policy (`Only a supervisor can do this`); non-supervisor decides an escalated claim; approval above the user's limit; adjuster assigns a task to someone else or takes a supervisor-queue task | `auth.writer`, `auth.supervisor`, `routes.review_claim`, `routes.assign_task` |
| 404 | Unknown claim, document, policy, policy version or review task; no analysis yet; no evaluation report; industry benchmark not generated | `routes._claim`, `routes._policy` and handlers |
| 409 | Claim already approved or rejected (upload, correction, analysis, review); review without an AI recommendation; letter without a successful analysis; task not open; task or claim assigned to someone else | `routes.py` |
| 422 | Pydantic validation; policy number not in the register; invalid fact correction; review action unknown or notes missing; upload validation; policy terms not JSON; policy ingestion failed | `routes.py`, `services.py` |
| 429 | Sign-in throttled, with `Retry-After` | `routes.login`, `auth.LoginThrottle` |
| 500 | Unhandled exception, including a database failure in `/ready` | `main.unhandled` |

## Analysis pipeline

### Safe failure

Agents are bounded functions called in a fixed order by `backend/app/agents/supervisor.py`. An agent that cannot proceed safely raises `AgentError` (`backend/app/agents/base.py`). Raise sites:

| Agent | Message | File |
|---|---|---|
| Intake | `No documents uploaded; upload claim documents before analysis.` | `agents/intake.py` |
| Intake | `Policy number <n> not found in the policy register.` | `agents/intake.py` |
| Intake | `Incident date missing or unreadable in claim documents.` | `agents/intake.py` |
| Policy Retrieval | `No <product> wording version is in force on <date>.` | `agents/policy.py` |

When an `AgentError` is raised, `analyze_claim`:

1. stores an `agent_runs` row for that agent with status `FAILED`, the error as its summary, the tool calls made so far and the duration;
2. sets the `analysis_runs` row to `FAILED` with `error` = `<agent name>: <message>` and `finished_at`;
3. sets the claim status to `NEEDS_ATTENTION`;
4. writes an `ANALYSIS_FAILED` audit event (actor `supervisor`) with the agent and error, under the run's correlation ID;
5. commits and returns. No AI decision is recorded and no new review task is created.

The HTTP call still returns 200 with the analysis object (`status: "FAILED"`, `error`, `result: null`). The claim page shows "Analysis stopped safely: <error>".

Other things that are not failures but stop short of a confident answer are handled inside the agents as outcomes, not errors: coverage `UNCERTAIN` or missing documents lead to a `REQUEST_INFO` recommendation, high risk to `INVESTIGATE` (`recommend` in `backend/app/agents/evidence.py`).

### Unexpected exceptions

The supervisor catches only `AgentError`. Any other exception propagates to the global handler (500 `INTERNAL_ERROR`). The request's database session closes without a commit (`backend/app/db.py`), so the run, its agent rows and the `ANALYSIS_STARTED` event are rolled back and the claim keeps its previous status.

### Run and claim states

| Object | States | Source |
|---|---|---|
| `analysis_runs.status` | `RUNNING` (model default, only inside the transaction), `SUCCEEDED`, `FAILED` | `models.py`, `supervisor.py` |
| `agent_runs.status` | `SUCCEEDED`, `FAILED` | `supervisor.py` |
| Claim status | `SUBMITTED` → `DOCUMENTS_RECEIVED` (first upload) → `ANALYZING` → `PENDING_REVIEW` or `NEEDS_ATTENTION`; reviewer actions set `APPROVED`, `REJECTED`, `INFO_REQUESTED`, `UNDER_INVESTIGATION` or `ESCALATED` | `services.add_document`, `supervisor.py`, `agents/review.py` |
| Workflow task | `OPEN`, `SUPERSEDED` (a later successful run replaced it), `CLOSED` (approve or reject) | `agents/review.py` |

Re-running is safe: each run is a new `analysis_runs` row; a successful run supersedes open tasks and adds a new AI decision. A failed run leaves any earlier open task as it was. Decided claims (`APPROVED`, `REJECTED`) cannot be re-analysed (409); reopening is not supported.

## Policy ingestion

`ingest_policy_file` (`backend/app/services.py`) records every attempt in `policy_ingestions` with timestamped stages: `UPLOADED`, `VALIDATING`, `EXTRACTING`, `INDEXING`, then `READY` or `FAILED`.

A `ValidationProblem` at any stage:

1. sets `error`, appends a `FAILED` stage with the reason and sets `finished_at`;
2. writes `POLICY_INGESTION_FAILED` (actor, ingestion ID, file, error);
3. raises `IngestionFailed`. The route commits so the failed record and its event are kept, then returns 422 `Ingestion #<id> failed: <reason>`.

Reasons, by stage:

| Stage | Reasons |
|---|---|
| Validating | Not `.pdf`, `.md` or `.txt`; empty; larger than `MAX_UPLOAD_BYTES`; same SHA-256 as a `READY` ingestion; terms missing required fields; effective dates not ISO or reversed; product version already exists |
| Extracting | PDF unreadable or encrypted; PDF has no text layer ("OCR is not available in this build"); text not UTF-8; no clauses found; terms cite clauses that are not in the wording |

Terms that are not a JSON object are rejected by the route (422) before any ingestion record is created. Instruction-like lines in a wording are not errors: they are stored as `warnings` and ignored. The retrieval index is rebuilt only after a successful ingestion.

## Claim document uploads

`add_document` (`services.py`) raises `ValidationProblem`, which the route turns into 422:

| Check | Message |
|---|---|
| Extension not `.pdf`, `.txt` or `.md` | `Unsupported file type for <name>. Upload PDF or text documents.` |
| Over `MAX_UPLOAD_BYTES` | `<name> is larger than 10 MB.` (with the configured size) |
| Empty | `<name> is empty.` |
| Text extraction fails | `Could not read <name>: <reason>` |

The filename is reduced to its base name. Files are processed in order; the first invalid file rolls back the database changes for the whole request. The stored copy of a file is written before text extraction, so a file that fails extraction (or a valid file earlier in a failed batch) can remain in `CLAIMSENSE_STORAGE_DIR` without a database row. Closed claims refuse uploads with 409.

## Sign-in throttle

`LoginThrottle` (`backend/app/auth.py`) counts failed sign-ins per `<client address>|<username>`. After `LOGIN_MAX_FAILURES` (5) failures inside `LOGIN_WINDOW_SECONDS` (300), sign-in returns 429 with `Retry-After` in seconds and writes `LOGIN_THROTTLED`. A successful sign-in clears the count. The state is in process memory: it resets on restart and is not shared between instances.

## Retrieval and the optional LLM

- The assistant refuses rather than guesses: below `RAG_MIN_SCORE`, or when the clause shares only generic insurance words with the question, the response has `grounded: false`, `mode: "refusal"` (`backend/app/rag/service.py`). This is a normal 200 response.
- The LLM call (`backend/app/llm.py`) has a 20-second timeout and no retry. Any failure is logged as a warning on `claimsense.llm` and the extractive answer is returned instead.
- Clauses whose provenance does not resolve are kept out of the index with a warning on `claimsense.rag`; start-up does not fail (`docs/DECISIONS.md`, D18).

## Readiness

`GET /api/v1/ready` runs `SELECT 1` and a one-clause retrieval. A database error surfaces as 500. An empty index is not an error: the response is 200 with `policy_index: "empty"`. The smoke test and CI treat anything other than `"ok"` as a failure.

## Frontend

`request()` in `frontend/src/api.ts`:

| Situation | Behaviour |
|---|---|
| Network failure | Throws `ApiError` with status 0: "Cannot reach the Claim Sense API. Check that the backend is running." |
| Non-2xx response | Throws `ApiError` with `error.message` from the body (or `Request failed (<status>)`) and the correlation ID from the body or the `x-correlation-id` header |
| 401 on any call except login | Clears the stored token and fires `claimsense:signed-out`; `App.tsx` returns to the sign-in screen |
| CSV export | Fetched directly; a non-2xx becomes `ApiError` "Export failed (<status>)" |

Pages use `useLoad` (`frontend/src/components/ui.tsx`) for data and `ErrorBox` for errors. `ErrorBox` shows the message, the correlation ID when known, and a **Retry** button when the page passes one. Forms keep their input after an error. Specific cases:

- **Claim workspace**: a failed upload, analysis, correction, review or letter shows the error in place; a run stopped by an agent shows "Analysis stopped safely: …".
- **New claim**: an error after the claim was created leaves the claim in place without its documents or analysis; the form shows the error.
- **Claims list**: CSV export errors use a browser `alert`.
- **Data sources**: a failed benchmark call (for example 404 before `scripts/fetch_public_data.py` has run) shows its message inside the benchmark card; the rest of the page still loads.
- **Documents tab**: opening a document's text has no error handler, so a failure is silent.
- Empty states are listed per screen in `UX_FLOWS.md`.

## Retries and timeouts

There are no automatic retries anywhere in the application, and no request timeouts on the frontend's `fetch` calls or on API handlers. Analysis and policy ingestion run synchronously inside the request; there is no job queue (`docs/DECISIONS.md`, D16). What does exist:

| Mechanism | Setting | Where |
|---|---|---|
| Manual retry | **Retry** button on load errors | `ErrorBox` |
| LLM call timeout | 20 s, falls back to extractive | `backend/app/llm.py` |
| Stale database connections | `pool_pre_ping=True` | `backend/app/db.py` |
| App waits for PostgreSQL | `depends_on: condition: service_healthy`; `pg_isready` every 5 s, 20 retries | `docker-compose.yml` |
| Container health check | `/api/v1/health` every 15 s, 5 s timeout, 20 s start period | `Dockerfile` |
| Smoke test HTTP timeout | 60 s per call; stops at the first failed check | `scripts/smoke_test.py` |
| Public data download | 120 s timeout, no retry; exits if the archive's SHA-256 differs from the pinned value or the CSV fails its schema or quality checks | `scripts/fetch_public_data.py` |
| Readiness polling | 60 × 2 s (CI), 60 × 5 s (Azure deploy, Verify deployment) | `.github/workflows/*.yml` |
| Browser suite | 60 s per test, `retries: 0` | `e2e/playwright.config.mjs` |

## Known gaps

- Unmatched routes do not use the uniform error body, and in the image unmatched GETs under `/api/v1` return the UI with 200.
- A failed analysis does not close or re-route an earlier open review task.
- Files from failed uploads can remain on disk.
- No retry, back-off or circuit breaker for the database or the LLM beyond what is listed above.
