# Data model — Claim Sense

SQLAlchemy 2 models in `backend/app/models.py`. SQLite by default (tests and local runs); PostgreSQL in Docker and the deployment. Tables are created at startup (`Base.metadata.create_all`), and the seeder is idempotent. Money is `Numeric(14,2)` and handled as `Decimal`.

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Synthetic demo accounts | `username`, `role` (ADJUSTER, SUPERVISOR, AUDITOR), `approval_limit`, `password_hash` (PBKDF2) |
| `policies` | Insurance products | `product_code`, `line_of_business`, `insurer`, `synthetic` |
| `policy_versions` | Effective-dated wording versions | `policy_id`, `version`, `effective_from`, `effective_to`, `source_file`, `terms` (JSON; every term cites a clause) |
| `policy_clauses` | Retrieval units with provenance | `version_id`, `clause_ref`, `title`, `section`, `page`, `text` |
| `policy_ingestions` | Every ingestion attempt and its processing states | `sha256`, `file_type`, `status` (UPLOADED → VALIDATING → EXTRACTING → INDEXING → READY / FAILED), `stages` (JSON), `pages`, `clauses`, `warnings`, `error` |
| `insured_policies` | Customer contracts | `policy_number`, `policy_id`, `holder_name`, `start_date`, `end_date`, `sum_insured` |
| `claims` | Claim header and status | `claim_number`, `policy_number`, `claim_type`, `incident_date`, `claimed_amount`, `status` |
| `claim_documents` | Uploaded files | `filename`, `doc_type`, `sha256`, `storage_path`, `text`, `pages` |
| `claim_facts` | Extracted facts with provenance | `document_id`, `name`, `value`, `confidence`, `source_line`, `source_text` |
| `analysis_runs` | One supervisor run per analysis | `correlation_id`, `status`, `policy_version_id`, `result` (JSON: facts, coverage, adjudication, risk, evidence, recommendation), `rules_version` |
| `agent_runs` | Bounded agent steps | `agent`, `status`, `summary`, `tool_calls` (JSON), `duration_ms` |
| `claim_decisions` | AI recommendations and human decisions | `source` (AI or HUMAN), `decision`, `payable_amount`, `actor`, `notes` |
| `workflow_tasks` | Review queues | `queue` (ADJUSTER_REVIEW, SIU_INVESTIGATION, PENDING_INFORMATION, SUPERVISOR_REVIEW), `priority`, `status`, `assignee` |
| `audit_events` | Append-only activity log | `claim_id` (nullable), `event_type`, `actor`, `details` (JSON), `correlation_id` |
| `dataset_sources` | Mirror of the validated `data/source_registry.json`; entries without provenance are not loaded | `name`, `publisher`, `year` (publication date), `url`, `purpose` (intended use), `status` |

## Relationships

- A policy has many versions; a version has many clauses.
- An insured policy belongs to a policy.
- A claim has many documents and facts, analysis runs (each with agent runs), decisions, workflow tasks and audit events.
- An analysis run records the policy version it used.

## Integrity rules

- **Structured terms:** must cite clauses that exist in the wording. Ingestion fails otherwise.
- **Duplicate wordings:** the same file is refused by checksum; the same product version is refused by key.
- **Re-runs:** a re-run supersedes the open workflow task; it never duplicates it.
- **Audit events:** only ever inserted.
