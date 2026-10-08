# Architecture

## Shape

A FastAPI modular monolith with a React single-page app. In production the UI is built into the same image and served by FastAPI, so one container serves everything. PostgreSQL in Docker Compose; SQLite for local development and tests.

## Analysis pipeline

`POST /api/v1/claims/{n}/analyze` runs the supervisor (`backend/app/agents/supervisor.py`):

| Order | Agent | Tools | Output |
|---|---|---|---|
| 0 | Document Intelligence (on upload) | `extract_text`, `classify`, `extract_facts` | Document type, facts with file, line and confidence, itemised charges |
| 1 | Intake | `consolidate_facts`, `lookup_policy_contract` | One claim view; fails safely if the policy or incident date is missing |
| 2 | Policy Retrieval | `match_policy_version`, `hybrid_rag_retrieve` | Wording version in force on the incident date; top clauses |
| 3 | Coverage | `evaluate_coverage_rules` | COVERED / NOT_COVERED / UNCERTAIN with cited findings and missing documents |
| 4 | Adjudication Tool | `adjudication_rules_engine` | Decimal waterfall, payable amount |
| 5 | Risk/Fraud | `risk_rules` | Score, level, signals, feature snapshot |
| 6 | Evidence | `build_evidence_package` | Evidence list and recommendation |
| 7 | Review/Workflow | `route_to_queue` | Workflow task in the right queue |
| 8 | Audit | – | `AI_RECOMMENDATION` event |

Each agent run is stored in `agent_runs` with its tool calls and duration. An `AgentError` stops the run, marks it FAILED and sets the claim to `NEEDS_ATTENTION`.

## Recommendation logic

1. Not covered → reject, citing the failing clause.
2. Missing documents or unassessable amount → request information.
3. High risk → investigate.
4. Payable below claimed → partial approval; otherwise approve.

A human always makes the final decision.

## Retrieval

Policy wording is Markdown with `<!-- page: N -->`, `## N. Section` and `### N.M Clause` markers. Each clause is a chunk with page, section and clause metadata. Two rankers are fused with weighted reciprocal rank fusion: BM25 over stemmed words (weight 1.5) and TF-IDF cosine over character 3–5 grams (weight 1.0). A small insurance synonym map expands lay terms ("drunk" → alcohol, influence). Answers below `RAG_MIN_SCORE` are refused.

## Data model

`policies`, `policy_versions` (effective dates, structured `terms`), `policy_clauses`, `insured_policies`, `claims`, `claim_documents`, `claim_facts`, `analysis_runs`, `agent_runs`, `claim_decisions` (AI and HUMAN), `workflow_tasks`, `audit_events`, `dataset_sources`. Money is `Numeric(14,2)`.

## Structured terms

The rules engine reads each version's `terms` JSON (deductible, co-pay, per-day limits, waiting periods, exclusion keywords, depreciation tables, required documents). Every term names the clause that states it, and ingestion rejects terms that cite a clause missing from the wording.
