# UX flows

How a user moves through the screens in `frontend/src/pages` to work a claim, a policy, an analysis, a review and the audit trail. Every screen calls the API through `frontend/src/api.ts`; endpoint details are in `API.md`.

## Roles

Roles are enforced on the server (`backend/app/auth.py`, `backend/app/api/routes.py`, `backend/app/agents/review.py`). The UI hides or disables what a role cannot do, using `can_write` and `is_supervisor` from `/auth/me`.

| Capability | Adjuster | Supervisor | Auditor |
|---|---|---|---|
| View dashboard, claims, claim workspace, review queue, policies, assistant, audit, evaluation, data sources, guide | Yes | Yes | Yes |
| Create claims, upload documents, correct facts, run analysis | Yes | Yes | No (read-only, 403) |
| Approve | Up to ₹2,00,000 (`DEMO_USERS` in `auth.py`) | No limit | No |
| Reject, request information, investigate, escalate | Yes, with notes for reject, investigate and escalate | Yes | No |
| Decide an `ESCALATED` claim | No | Yes | No |
| Decide a claim whose open task is assigned to someone else | No (409) | Yes | No |
| Take or release review tasks | Own tasks; not tasks in `SUPERVISOR_REVIEW` | Assign any task to any adjuster or supervisor | No |
| Ingest a policy wording | No | Yes | No |

Escalation (`apply_review` in `agents/review.py`) moves the open task to `SUPERVISOR_REVIEW`, HIGH priority, unassigned.

## Screens

| Route | Page | Main API calls |
|---|---|---|
| (signed out) | `Login.tsx` | `/auth/demo-info`, `/auth/login` |
| `/` | `Dashboard.tsx` | `/analytics`, `/claims` |
| `/claims` | `Claims.tsx` | `/claims`, `/claims-export.csv` |
| `/claims/new` | `NewClaim.tsx` (writers only; hidden from the auditor's menu) | `/insured-policies`, `/demo-packet`, `/claims`, `/claims/{n}/documents`, `/claims/{n}/analyze` |
| `/claims/:claimNumber` | `ClaimDetail.tsx` | `/claims/{n}`, documents, facts, analyze, review, letter |
| `/reviews` | `Reviews.tsx` | `/reviews`, `/reviewers`, `/reviews/{id}/assign` |
| `/policies` | `Policies.tsx` | `/policies`, `/policies/{code}/versions`, `/policy-ingestions`, `POST /policies` |
| `/assistant` | `Assistant.tsx` | `/policies`, `/rag/query` |
| `/audit` | `AuditLog.tsx` | `/audit` |
| `/evaluation` | `Evaluation.tsx` | `/evaluation` |
| `/datasets` | `Datasets.tsx` | `/datasets`, `/knowledge-base/manifest`, `/benchmarks/industry` |
| `/guide` | `Guide.tsx` | none (static content with links) |

The shell (`App.tsx`) shows the navigation, the signed-in user with role and approval limit, a **Sign out** button, and an API status line from `/ready` ("API ready · postgresql · LLM off", "Checking API…" or "API unreachable"). Below 980 px the navigation sits behind a **Menu** button. Unknown routes show "Page not found."

## 1. Sign in

1. The app reads the token from local storage (`claimsense.token`). If one exists it calls `/auth/me` and shows "Loading…" meanwhile; a failure clears the token.
2. Without a valid token the sign-in screen opens. It calls `/auth/demo-info`.
3. The user picks a demo account chip (adjuster, supervisor, auditor). The chip fills the password with the documented default only when `default_password` is true; otherwise it focuses the password field and the help text says the deployment uses its own `DEMO_PASSWORD`.
4. **Sign in** posts `/auth/login`. The button is disabled until a password is entered and shows "Signing in…" while waiting.
5. Errors appear in the error box: 401 "Wrong username or password", 429 "Too many failed sign-ins. Try again in N seconds."
6. Any later 401 from the API clears the token and returns the user to this screen (`claimsense:signed-out` event in `api.ts`).

## 2. Dashboard

1. The dashboard loads `/analytics` and `/claims` for the selected line of business and period. Both filters live in the URL (`?line=motor&days=30`).
2. Tiles (claims, pending review, high risk, overdue settlement, decided) and bars (recommendations, risk levels, statuses) link to `/claims` with the matching filters, keeping the dashboard's line and period.
3. Other cards: weekly trend, needs attention (links to the claim and to `/reviews`), open claims by age, decline reasons with clauses, work queues, workload, amounts by line, and the synthetic portfolio evaluation, with a toggle between the 1,000-claim health and motor portfolio and the 10,000-claim six-line portfolio (precision and recall per line and per injected pattern).
4. A first-visit notice points to the guide; **Dismiss** remembers it in local storage (`claimsense.intro-dismissed`).
5. States: "Loading…" until analytics arrive; an error box with **Retry** if they fail; "No data for this selection." for empty bars; "No claims in this selection." for the recent-claims table.

## 3. Claim journey

### 3.1 Find a claim

1. `/claims` lists claims newest first. Search and the status, line, recommendation, risk and settlement filters are URL parameters, so dashboard drill-downs and shared links open the same list.
2. Active filters show as removable tags; **Clear all filters** resets them. Columns sort on click.
3. Clicking a row opens the claim workspace.
4. **Export CSV** downloads the claim register; a failure shows a browser alert.
5. States: "Loading…", error box with **Retry**, "No claims match these filters."

### 3.2 Create a claim (adjuster or supervisor)

1. Open **New claim**. The policy list comes from `/insured-policies`.
2. Either fill the form (policy, claim type, claimant, description, documents) or pick a line in the sample selector (health, travel, home, personal accident, life) and press **Use the sample packet**, which loads that synthetic packet and its files from `/demo-packet?line=…`.
3. Press **Create claim** (no files) or **Create, upload and analyse**. The page runs three calls in turn and shows progress text: "Creating claim…", "Uploading and extracting N document(s)…", "Running the agent pipeline…".
4. On success the claim workspace opens.
5. On failure the error box shows the API message and correlation ID, and the form stays filled. If creation succeeded and a later step failed, the claim already exists; open it from `/claims` to continue.
6. Choosing a policy fills the claimant name and sets the claim type to the policy's line (`line_of_business` from `/insured-policies`). The server still rejects a policy number that is not in the register and a claim type that differs from the policy's line (422).

### 3.3 Documents and facts

1. In the workspace, **Upload documents** (writers, claim not closed) posts files; the claim reloads with the new documents.
2. The **Documents** tab lists each document with its detected type; clicking a file name shows its extracted text.
3. **Extracted claim facts** lists the facts the next analysis will use, each with its source file, line and confidence.
4. **Correct** opens an inline form: new value and reason are both required. Saving records the correction; the extracted value stays visible next to a "Corrected" badge.
5. If facts changed after the last analysis, a notice says "Re-run the analysis to apply."
6. Empty states: "No documents yet…", "No facts extracted yet.", and line items wait for the analysis.

## 4. Analysis journey

1. **Run AI analysis** (or **Re-run analysis**) is shown to writers on open claims and is disabled until at least one document exists. While it runs the page shows "Running agents…".
2. The supervisor runs the pipeline (`backend/app/agents/supervisor.py`). On success the claim moves to `PENDING_REVIEW` and a review task opens.
3. If an agent stops the run (for example, no wording in force on the incident date), the page shows "Analysis stopped safely: <agent>: <reason>" and the claim shows `NEEDS_ATTENTION`. Fix the cause (correct a fact, upload a document) and re-run.
4. Results are spread over the workspace tabs, each with a count where it applies and a deep link (`/claims/CLM-H-1002#coverage`):

| Tab | Shows | Before analysis |
|---|---|---|
| Overview | Recommendation, amounts (claimed, billed, payable), policy version, coverage, risk, settlement clock, agent pipeline with run ID, correlation ID, durations and tool calls | Prompt to upload documents or run the analysis |
| Documents | Documents, facts, line items | Line items placeholder |
| Policy & evidence | Policy in force and why, evidence package with expandable clause citations | "Run the AI analysis to see this section." |
| Coverage | Each check as pass, fail or missing, with its clause | Same |
| Adjudication | Rule-by-rule waterfall with clause references and the payable amount | Same |
| Risk | Score, level and each signal with its weight | Same |
| Review | Human review panel, decisions, workflow task, decision letter | Decisions list only |
| Audit | Every event for the claim | Events so far |

## 5. Review journey

1. A writer opens a claim from the review queue (`/reviews` links to `#review`) or from the Overview's **Open review** prompt, shown while a decision is pending.
2. The **Human review** panel shows the reviewer, an editable approved amount (pre-filled with the AI payable) and a notes box.
3. Actions: **Approve**, **Reject**, **Request info**, **Investigate**, **Escalate**.
   - Reject, investigate and escalate need notes; the server returns 422 otherwise.
   - If the amount is above the user's limit, a notice explains it and **Approve** is disabled; the adjuster escalates instead.
   - On an escalated claim a non-supervisor sees "This claim is escalated. A supervisor must decide it." and every action is disabled.
4. After the action the claim reloads with the new status and the decision in the **Decisions** list.
5. **Generate letter** builds the claimant letter from the stored decision. It is marked DRAFT until a human decides, then FINAL. **Print** prints it.
6. Approved and rejected claims are closed: upload, analysis, correction and review controls disappear. Reopening is not supported (409).
7. Auditors see the claim but no review panel ("You can view this claim but not decide it.").

### Review queue

1. `/reviews` lists open tasks by priority, then age, with views **All open**, **Assigned to me**, **Unassigned**.
2. Adjusters see **Take** on unassigned tasks outside the supervisor queue and **Release** on their own. Supervisors get a drop-down per task to assign anyone or unassign.
3. Errors from assignment (for example, someone else took the task first) appear in the error box. Empty view: "Nothing here."

## 6. Policy journey

1. `/policies` shows one card per product with its versions, effective dates and clause counts.
2. Selecting a product shows the latest version's clauses; a version selector and a clause filter narrow it. **Structured terms used by the rules engine** expands the terms JSON.
3. Supervisors see **Ingest a policy wording**: choose a wording (PDF, Markdown or text) and a terms JSON, then **Ingest and index**. Success shows "Ingested <code> v<version>: N clauses on P pages indexed." and the processing stages. Failure shows the reason in the error box, and the failed attempt is kept with its stages.
4. Other roles see "Supervisors can ingest new policy wordings."
5. **Ingestion history** lists the last 50 attempts with status, stages, warnings for ignored instruction-like lines, and the actor. Empty: "No ingestions yet."

### Policy assistant

1. `/assistant` takes a question (at least 3 characters) and an optional product and version, or one of the example chips.
2. A grounded answer shows its mode (extractive, or LLM when `ANTHROPIC_API_KEY` is set) and the cited clauses with page, scores and ranks.
3. If the wording does not answer the question, the card reads "No sufficient evidence" and lists the closest clauses below the threshold.

## 7. Audit journey

1. `/audit` shows the latest 100 events across the system: time, event type, claim (linked), actor, details and correlation ID.
2. Each claim's **Audit** tab shows all events for that claim, in order.
3. Pipeline events carry the analysis run's correlation ID, which also appears on the Overview's agent pipeline card, so a reviewer can match events to a run.
4. States: "Loading…", error box with **Retry**.

## 8. Evaluation, data sources and guide

- **Evaluation** (`/evaluation`) shows the committed golden evaluation report: checks passed, claim cases, policy questions, retrieval hit@1 and MRR, then each case with expandable checks. 404 when no report exists appears in the error box.
- **Data sources** (`/datasets`) shows the source registry (validated with checksums on each request), the CAS Schedule P industry benchmark next to its registry entry, and the RAG manifest (indexed and rejected chunks). Errors from the registry or manifest call show one error box with **Retry**; a benchmark error (for example 404 when the aggregates were not generated) shows its message inside the benchmark card.
- **How to use** (`/guide`) lists the demo accounts, a six-step tour with links, and seeded claims worth opening.

## Shared states

| State | Component | Where |
|---|---|---|
| Loading | `Loading` ("Loading…") | Initial token check, every list and detail page |
| Error | `ErrorBox`: message, correlation ID when present, optional **Retry** | Every page that loads data, and every form |
| API unreachable | `ApiError` with status 0: "Cannot reach the Claim Sense API. Check that the backend is running." | Any call (`api.ts`) |
| Busy | Disabled buttons and progress text | Sign-in, new claim, analysis, upload, review, assignment, assistant |
| Empty | Inline muted text in tables and cards | See each flow above |

## Notes found while writing this

- Clicking a document name in the Documents tab has no error handling; a failed fetch is not shown to the user.
