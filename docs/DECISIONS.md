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
| D10 | No authentication in v1; reviewer name is free text | Not in the prioritised golden path; listed as the first roadmap item |
