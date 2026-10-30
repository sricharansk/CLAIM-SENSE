# Roadmap

From MVP to intelligence to enterprise expansion, as the blueprint frames it (`docs/Claim_Sense_Project_1_..._FINAL_V2_...md`, PART 2 and PART 17). The blueprint does not number releases; this document groups its items into four stages:

| Stage | Blueprint source |
|---|---|
| **V1 MVP** | The golden path and definition of done (PARTs 16 and 20, Prompts 01–20) |
| **V2 Intelligence** | Deferred AI and data work: OCR fallback, embeddings, Azure AI Search, ML risk model, current public datasets; extension Stages 2 and 3 (advanced RAG evaluation, reranking, larger corpora, MLflow, drift monitoring) |
| **V3 Enterprise** | Extension Stages 1 and 4: Azure deployment, managed identity, secret management, cloud observability, enterprise IAM, multi-tenant review, load testing, backup and DR; the PART 17 target architecture (Blob Storage, Key Vault, worker) and AKS |
| **V4 Advanced** | Extension Stage 5 and the *Enterprise-later* list: core-system integrations, compliance review, production data governance, advanced MLOps, multi-region DR, network isolation |

Status is judged from the code and `docs/IMPLEMENTATION_STATUS.md`:

- **Done**: in this repository and covered by a test, the evaluation, the smoke test or the browser suite.
- **Partly**: some of it is built, or it is built but not exercised.
- **Not started**: no code for it.

## V1 MVP

| Item | Status | Evidence |
|---|---|---|
| Sign-in, three roles, approval limit, escalation | Done | `backend/app/auth.py`, `api/routes.py`, `test_auth.py` |
| Policy ingestion from PDF or Markdown with checksum and processing states | Done | `services.ingest_policy_file`, `test_policy_ingestion.py` |
| Effective-dated policy versions and version matching | Done | `agents/policy.py`, `policy_versions` |
| Claim intake, document upload and rule-based extraction with source line and confidence | Done | `agents/document.py`, `services.add_document`, `test_extraction.py` |
| Reviewer correction of extracted facts | Done | `POST /claims/{n}/facts`, `test_fact_correction.py` |
| Hybrid retrieval (BM25 + character n-gram TF-IDF, RRF) with clause, page and version citations; refusal on weak evidence | Done | `rag/retriever.py`, `rag/service.py`, `test_rag.py` |
| Coverage and exclusion checks citing clauses | Done | `agents/coverage.py` |
| Deterministic Decimal adjudication waterfall | Done | `adjudication/rules.py`, `test_adjudication.py` |
| Risk and fraud signals (rules), including duplicate and embedded-instruction checks | Done | `agents/risk.py`, `safety.py`, `test_security_guards.py` |
| Evidence-backed recommendation; supervisor with bounded agents and safe failure | Done | `agents/evidence.py`, `agents/supervisor.py` |
| Human review, review queue with take, release and reassign | Done | `agents/review.py`, `test_review_assignment.py` |
| Audit of every pipeline stage and decision | Done | `audit_events`, `test_golden_path.py` |
| Dashboard with filters and drill-down; claim workspace with eight tabs | Done | `frontend/src/pages`, Playwright suite in `e2e/` |
| Decision letters, settlement clock, CSV export | Done | `letters.py`, `sla.py`, `test_letters_sla.py` |
| Golden evaluation | Done | `scripts/evaluate.py`; the committed `reports/evaluation.json` records 986 / 986 checks over 72 claim cases and 30 questions |
| Data provenance registry and RAG manifest | Done | `data/source_registry.json`, `provenance.py`, `test_provenance.py` |
| Docker image and Compose stack with PostgreSQL | Done | `Dockerfile`, `docker-compose.yml`, CI `docker-smoke` |
| CI: lint, tests, evaluation, provenance, dependency audits, build, browser suite, smoke test | Done | `.github/workflows/ci.yml` |
| Cloud deployment with a passing signed-in smoke test | Done | Render (`render.yaml`, https://claim-sense.onrender.com); the **Verify deployment** workflow's signed-in smoke test passed (runs 38358451765, 38685398836 and 41102353747, `IMPLEMENTATION_STATUS.md`) |

## V2 Intelligence

| Item | Status | Evidence |
|---|---|---|
| More lines of business: property (home), travel, personal accident, life | Done | Wordings `HOME-GUARD`, `TRV-GLOBE`, `PA-SECURE` and `LIFE-TERM` 2025.1 in `data/policies/`; indemnity waterfalls and the benefit-schedule model in `adjudication/rules.py`; seeded claims CLM-P-3001…, CLM-T-4001…, CLM-A-5001… and CLM-L-6001… from `data/synthetic/generate.py`; `test_property_travel.py`, `test_benefit_lines.py` |
| Industry loss-reserving benchmarks (CAS Schedule P) by line | Done | `scripts/fetch_public_data.py`, `data/public/cas_schedule_p/benchmark.json`, `GET /api/v1/benchmarks/industry`, Data sources screen. External context only; not used in any claim decision |
| Every seeded claim and evaluation packet run through the real pipeline at start-up | Done | `seed.py`, `test_seed_packets.py` (72 claims, D25) |
| Optional LLM-worded assistant answers | Partly | `backend/app/llm.py` is wired and falls back safely; never run here because no `ANTHROPIC_API_KEY` was provided |
| Advanced RAG evaluation | Partly | Golden evaluation reports hit@1, hit@3, MRR and refusal accuracy; no retrieval monitoring in production |
| Ingest current public datasets (IRDAI circulars and others) | Partly | One public dataset is in use (CAS Schedule P, aggregates only). The other 9 public sources in `data/source_registry.json` are registered with dates and licence status but not downloaded or ingested, including the IRDAI circulars (`IMPLEMENTATION_STATUS.md`, *Blocked*) |
| OCR for scanned documents and wordings | Not started | Scanned PDFs fail with "OCR is not available in this build" (`services.py`) |
| Embeddings retriever (dense vectors as a third ranker) | Not started | `DECISIONS.md` D3 |
| Reranking | Not started | – |
| Azure AI Search | Not started | – |
| ML fraud model | Not started | Risk is weighted rules (`DECISIONS.md` D8); the portfolio evaluation (10,000 synthetic claims on six lines) measures how well the rules recover injected patterns only (`analytics.portfolio_evaluation`) |
| LLM-assisted extraction | Not started | Extraction is rule-based (`DECISIONS.md` D7) |
| Model registry, drift monitoring, retraining gates (MLflow) | Not started | – |

## V3 Enterprise

| Item | Status | Evidence |
|---|---|---|
| Azure Container Apps deployment | Partly | `.github/workflows/deploy-azure.yml` exists; not run (`docs/DEPLOYMENT.md`) |
| Managed PostgreSQL | Partly | Supported through `DATABASE_URL` and tested on PostgreSQL in Compose; no managed instance provisioned |
| Single sign-on and user management | Not started | Three seeded accounts share `DEMO_PASSWORD` (`docs/SECURITY.md`) |
| Token revocation | Not started | Tokens are stateless (`auth.py`) |
| Secret management (Key Vault) and managed identity | Not started | Secrets are environment variables |
| Cloud observability (Application Insights / Azure Monitor) | Not started | `docs/OBSERVABILITY.md` |
| Background job queue for analysis and ingestion | Not started | Both run inside the request (`DECISIONS.md` D16) |
| Object storage (Blob) for documents | Not started | Files go to `CLAIMSENSE_STORAGE_DIR` on local disk or a volume |
| Shared sign-in throttle and general rate limiting | Not started | Throttle is in-process (`auth.LoginThrottle`) |
| Upload malware scanning | Not started | `docs/SECURITY.md`, *Known gaps* |
| Reopening decided claims | Not started | Returns 409 (`routes.analyze`) |
| Multi-tenant isolation review, load testing, backup and restore, disaster recovery | Not started | – |
| AKS scale-out | Not started | – |

## V4 Advanced

| Item | Status |
|---|---|
| Insurer core-system integrations | Not started |
| Formal compliance and legal review | Not started |
| Production data governance (real data) | Not started; the repository uses synthetic data only |
| Proprietary insurer fraud training | Not started |
| Advanced MLOps retraining | Not started |
| Multi-region disaster recovery | Not started |
| Enterprise network isolation | Not started |
| High-volume performance certification | Not started |

Unrestricted autonomous adjudication is on the blueprint's *Enterprise-later* list but conflicts with this project's rule that humans make the final decision (`CLAUDE.md`, `docs/DECISIONS.md`). It is not planned.
