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
