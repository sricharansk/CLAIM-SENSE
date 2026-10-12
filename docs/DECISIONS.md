# Decisions

| # | Decision | Why |
|---|---|---|
| D1 | FastAPI modular monolith with agents as in-process modules | Blueprint §4.2: keep the agentic design without microservice overhead in the sprint |
| D2 | Coverage and adjudication are deterministic, driven by structured terms that cite clauses | Blueprint: no LLM arithmetic, no invented clauses; results are reproducible and testable |
| D3 | Hybrid lexical retrieval (BM25 + char n-gram TF-IDF) instead of a hosted embedding model | Runs offline with no key or model download; embeddings can be added as a third ranker |
| D4 | LLM optional (Anthropic), off by default; extractive answers otherwise | No key was provided; the product must still work and never fabricate |
| D5 | Vite + React instead of Next.js | Smaller build, served as static files by FastAPI in one container |
| D6 | SQLite by default, PostgreSQL in Docker | Zero-setup local runs and tests; production-like database in Compose |
| D7 | Rule-based extraction from labelled fields and itemised lines | Deterministic provenance (file + line); OCR and LLM extraction are roadmap items |
| D8 | Duplicate detection and other risk signals are weighted rules, not ML | Transparent and explainable for reviewers; ML is roadmap |
| D9 | Claim numbers are the public identifier in URLs and APIs | Readable for reviewers and audit |
| D10 | Built-in sign-in with three seeded roles and signed tokens instead of an identity provider | Works in any deployment with no external setup; SSO (Azure AD / OIDC) is the next step |
| D11 | Adjuster approval limit of ₹2,00,000; escalated claims only a supervisor can decide | Mirrors common delegated-authority limits in claims operations and keeps high-value payouts under senior review |
| D12 | Decision letters are filled from templates and stored data, never written by an LLM | A customer-facing repudiation must quote the exact clause and amounts; templates make that verifiable. Letters stay marked draft until a human decides |
| D13 | Settlement clock counts from the last document upload, using the policy's `settlement_days` term | The synthetic wordings define settlement within 30 days of the last required document, so the clock follows the wording rather than a hard-coded SLA |
| D14 | Evaluation expectations are worked out by hand from the wording and terms, and the report is committed and served read-only | A scorecard that copies system output proves nothing; the hand working is in `data/evaluation/golden_cases.json` so a reviewer can check it |
| D15 | The assistant refuses when retrieved clauses share only generic insurance words with the question | Score thresholds alone answered off-topic and instruction-like prompts from loosely related clauses |
| D16 | Policy ingestion runs synchronously but records each processing state with a timestamp per attempt | The staged history is visible and auditable without a job queue; a background worker can drive the same states later |
| D17 | The source registry is JSON (`data/source_registry.json`), not the YAML file the blueprint names | The backend already reads JSON and has no YAML parser; the fields and the validator are what the blueprint asks for |
| D18 | The retrieval index excludes any chunk whose provenance does not resolve, instead of failing start-up | One bad version should not take the assistant down; the rejected chunks are listed in the manifest and fail the CI check |
| D19 | Property and travel reuse the same pipeline; only terms, extraction vocabulary and one rules function per line are new | The agents, evidence, review and audit stay line-agnostic, so a new line is data plus a deterministic waterfall, and health and motor results are unchanged |
| D20 | Item categories are looked up per line for property and travel; health and motor keep the original list | The same word means different things ("laptop" is home contents or lost baggage, "room" is ward or hotel); a per-line table avoids cross-line misreads without re-categorising existing claims |
| D21 | Documents that depend on the loss (police report for burglary, airline report for lost baggage, medical report for treatment abroad) are listed in the terms with trigger words | The wordings make them conditional; deriving the requirement from the claim text keeps the check deterministic and cited to the documents clause |
| D22 | Travel risk scoring ignores the early-claim signal | A trip policy starts at departure, so a loss soon after the start is expected and would mark every travel claim as riskier |
| D23 | The pre-existing disease waiting period is applied when the claim documents name the condition as pre-existing, declared at proposal or a known case | Extraction has no medical history beyond the documents; reading what the treating hospital wrote keeps the check deterministic and cited to §3.2, and a reviewer can correct the facts before re-running |
| D24 | Every exclusion, waiting period, limit and loss-dependent document in a wording has at least one seeded claim with a hand-worked golden case | A rule no claim exercises is a rule nobody has checked; the audit that introduced this found the pre-existing disease period unenforced |
| D25 | The deployed app also seeds the 7 evaluation packets as claims (`CLAIMSENSE_SEED_PACKETS`); the evaluation, the claims report and the tests turn it off | A reviewer opening the demo should see every packet the results report covers, but the evaluation files the same packets fresh through the API to test the upload path, and a seeded copy would make each one a duplicate |
| D26 | A loss outside the policy period is rejected citing the wording's coverage clause | The pass case already cited it; an adverse decision must quote a clause, and the coverage clause is where the wording grants cover during the policy period |
