# UX flows

How a user moves through the screens in `frontend/src/pages` to work a claim, a policy, an analysis, a review and the audit trail. Every screen calls the API through `frontend/src/api.ts`; endpoint details are in `API.md`.

## Roles

Roles are enforced on the server (`backend/app/auth.py`, `backend/app/api/routes.py`). The UI hides or disables what a role cannot do, using `can_write` and `is_supervisor` from `/auth/me`.

| Capability | Adjuster | Supervisor | Auditor |
|---|---|---|---|
| View dashboard, claims, claim workspace, review queue, policies, assistant, audit, evaluation, data sources | Yes | Yes | Yes |
| Create claims, upload documents, correct facts, run analysis | Yes | Yes | No (read-only, 403; **New claim** is hidden) |
| Approve | Up to ₹2,00,000 (`DEMO_USERS` in `auth.py`) | No limit | No |
| Reject, request information, investigate, escalate | Yes, with notes for reject, investigate and escalate | Yes | No |
| Decide an `ESCALATED` claim | No | Yes | No |
| Decide a claim whose open task is assigned to someone else | No (409) | Yes | No |
| Take or release review tasks | Own tasks; not tasks in `SUPERVISOR_REVIEW` | Assign any task | No |
| Ingest a policy wording | No | Yes | No |

## Screens

| Route | Page | Main API calls |
|---|---|---|
| (signed out) | `Login.tsx` | `/auth/login` |
| `/` | `Dashboard.tsx` | `/analytics`, `/claims` |
| `/claims` | `Claims.tsx` | `/claims`, `/claims-export.csv` |
| `/claims/new` | `NewClaim.tsx` (writers only) | `/insured-policies`, `/claims`, `/claims/{n}/documents`, `/claims/{n}/analyze` |
| `/claims/:claimNumber` | `ClaimDetail.tsx` | `/claims/{n}`, documents, facts, analyze, review, letter |
| `/reviews` | `Reviews.tsx` | `/reviews`, `/reviewers`, `/reviews/{id}/assign` |
| `/policies` | `Policies.tsx` | `/policies`, `/policies/{code}/versions`, `/policy-ingestions`, `POST /policies` |
| `/assistant` | `Assistant.tsx` | `/policies`, `/rag/query` |
| `/audit` | `AuditLog.tsx` | `/audit` |
| `/evaluation` | `Evaluation.tsx` | `/evaluation` |
| `/datasets` | `Datasets.tsx` | `/datasets`, `/knowledge-base/manifest`, `/benchmarks/industry` |

The shell (`App.tsx`) shows the navigation, the signed-in user with role and approval limit, a **Sign out** button, and an API status line from `/ready` ("API ready · postgresql · LLM off", "Checking API…" or "API unreachable"). On a narrow screen the navigation sits behind a **Menu** button. Unknown routes show "Page not found."

## 1. Sign in

1. The app reads the token from local storage. If one exists it calls `/auth/me` and shows "Loading…" meanwhile; a failure clears the token.
2. Without a valid token the sign-in screen opens. Three chips (adjuster, supervisor, auditor) fill the username and the documented default password `claimsense-demo`. A deployment with its own `DEMO_PASSWORD` needs that password typed in.
3. **Sign in** posts `/auth/login`. The button is disabled until a password is entered and shows "Signing in…" while waiting.
4. Errors appear in the error box: 401 "Wrong username or password", 429 "Too many failed sign-ins. Try again in N seconds."
5. Any later 401 from the API clears the token and returns the user to this screen (`claimsense:signed-out` event in `api.ts`).

## 2. Dashboard

1. Loads `/analytics` and `/claims`.
2. Tiles: claims, pending human review, high risk, decided, claimed, AI-recommended payable, average analysis time, override rate, escalation rate, settlement overdue. The first three link to `/claims` with the matching filter.
3. **Lines of business** lists each of the six lines with its claims, claimed and payable amounts; a line name opens `/claims?type=<line>`.
4. Bars for AI recommendations, reviewer actions, risk levels, claim status and the settlement clock. Recommendation, risk and status bars link to the filtered claims list.
5. **Recent claims** shows the eight newest. The portfolio card scores the 10,000-claim synthetic portfolio with the live risk rules (precision, recall, confusion counts).
6. States: "Loading…" until analytics arrive; an error box with **Retry** if they fail.

## 3. Claim journey

### 3.1 Find a claim

1. `/claims` lists claims newest first. Search (claim, claimant or policy number) and the status filter go to the server; `type`, `recommendation` and `risk` come from the URL and filter in the browser, so dashboard drill-downs open the same list.
2. Active URL filters show as removable chips with "Showing N of M claims where …".
3. **Export CSV** downloads the claim register; a failure shows a browser alert.
4. States: "Loading…", error box with **Retry**.

### 3.2 Create a claim (adjuster or supervisor)

1. Open **New claim**. The policy list comes from `/insured-policies`.
2. Choosing a policy fills the claimant name and sets the claim type from the product code (HLT health, MTR motor, HOME property, TRV travel, PA personal accident, LIFE life). The type can still be changed.
3. Press **Create claim** (no files) or **Create, upload and analyse**. The page runs the calls in turn and shows progress text: "Creating claim…", "Uploading and extracting N document(s)…", "Running the agent pipeline…".
4. On success the claim workspace opens. On failure the error box shows the API message and correlation ID, and the form stays filled. If creation succeeded and a later step failed, the claim already exists; open it from `/claims` to continue.

### 3.3 Documents and facts

1. In the workspace, **Upload documents** (writers, claim not closed) posts files; the claim reloads.
2. The **Documents** tab lists each document with its detected type, pages and upload time; clicking a file name shows its extracted text. "No documents yet." when empty.
3. **Extracted claim facts** shows each fact with its value and source. Writers can **Correct** a correctable fact with a reason. The correction is kept beside the extracted value, and a notice asks for a re-run until the analysis uses it.

### 3.4 Analysis

1. **Run AI analysis** (or **Re-run analysis**) posts `/claims/{n}/analyze` and shows "Running agents…".
2. A run stopped by an agent shows "Analysis stopped safely: <reason>" and the claim moves to `NEEDS_ATTENTION`.
3. On success the tabs fill in:
   - **Overview**: amounts (claimed, billed, payable), policy version, coverage, risk, evidence count, settlement, and the agent pipeline with each agent's duration and tool calls.
   - **Policy & evidence**: the wording version in force on the incident date and the cited clauses and facts.
   - **Coverage**: every check with PASS, FAIL or UNCERTAIN and its clause.
   - **Adjudication**: the waterfall (rule, step, adjustment, running total, clause, detail) and the payable amount. Personal accident and life claims show the scheduled benefit for each item (`R20_BENEFIT_SCHEDULE`).
   - **Risk**: score, level and each signal, or "No risk signals fired."
   - Tabs without a result say "Run the AI analysis to see this section."

### 3.5 Review and letter

1. The **Review** tab shows the AI recommendation, earlier decisions and the workflow task.
2. Writers choose **Approve**, **Reject**, **Request info**, **Investigate** or **Escalate**, optionally change the approved amount, and add notes (required to reject, investigate or escalate). The server enforces the approval limit, escalation and assignment rules; its message appears in the error box.
3. An auditor sees "You can view this claim but not decide it."; on an escalated claim a non-supervisor sees "This claim is escalated. A supervisor must decide it."
4. **Decision letter** generates a settlement, repudiation, document-request or under-review letter from the latest analysis and decision, quoting the clauses. **Print** prints it. Letters are marked as synthetic.

### 3.6 Audit

The **Audit** tab lists the claim's events with actor, details and the analysis run's correlation ID.

## 4. Review queue

1. `/reviews` lists open tasks by priority (HIGH, MEDIUM, NORMAL) then age, with queue, claim, status, risk, AI recommendation, AI payable, settlement due and assignee.
2. Views: **All open**, **Assigned to me**, **Unassigned**. "Nothing here." when empty.
3. **Take** and **Release** call `/reviews/{id}/assign`; a supervisor gets a reviewer selector on each task instead.

## 5. Policies and assistant

1. **Policy library** lists each product with its versions, effective dates and clause counts. Selecting a product shows the chosen version's clauses with section and page (with a clause filter) and, folded away, the structured terms the rules engine uses.
2. Supervisors see **Ingest a policy wording**: a wording (`.pdf`, `.md` or `.txt`) and its terms (`.json`), then **Ingest and index**. **Ingestion history** shows each attempt's processing states (UPLOADED, VALIDATING, EXTRACTING, INDEXING, READY or FAILED) and the reason for a failure.
3. **Policy assistant** answers a question, optionally limited to one policy and version, with cited clauses. When the evidence is too weak it says "No sufficient evidence" and lists the closest clauses below the threshold instead of guessing.

## 6. Audit trail, evaluation and data sources

1. **Audit trail** shows the latest 100 events across the system (append-only).
2. **Evaluation** shows the committed golden evaluation: checks passed, claim cases, policy questions, retrieval scores and every check with its expected and actual value.
3. **Data sources** shows the source registry with each source's checksum verified on request, the CAS Schedule P industry benchmark (loss ratio and paid development for six US lines, aggregates only, not used in any decision), and the RAG ingestion manifest. A failed benchmark call shows its message inside the benchmark card; the rest of the page still loads.
