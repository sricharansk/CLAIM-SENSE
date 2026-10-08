# Prompt 3 --- Can AI Agents Build Claim Sense in One Day?

## User Prompt

As I have only 2 hours to implement this project fully and convert into
product since the intern is going to over within days I need all these
to done 100 percent done fully will it be done using AI Agents like
claude code

## Answer

AI coding agents such as Claude Code can dramatically accelerate
implementation, but a fully production-ready insurance platform at 100%
completeness in one day is not realistic.

What is feasible is a **high-quality, end-to-end product MVP** that
works as a real product demonstration and has architecture prepared for
future production expansion.

## 1. One-Day Goal

Build one complete vertical slice:

``` text
Upload Policy PDF
      ↓
Upload Claim Documents
      ↓
Document Extraction
      ↓
RAG Retrieval
      ↓
Coverage Analysis
      ↓
Rule-Based Adjudication
      ↓
AI Recommendation
      ↓
Evidence + Policy Citations
      ↓
Human Review
      ↓
Approve / Reject / Escalate
```

If this entire workflow works through a UI, you have a demonstrable
product.

## 2. What AI Coding Agents Can Do

  Task                          AI Agent Capability
  ----------------------------- ---------------------------
  Project scaffolding           Yes
  Backend APIs                  Yes
  React UI                      Yes
  Database schema               Yes
  RAG pipeline                  Yes
  PDF processing                Yes
  Prompt engineering            Yes
  Docker                        Yes
  Unit tests                    Yes
  README                        Yes
  API documentation             Yes
  Debugging                     Yes
  Refactoring                   Yes
  Deployment configuration      Yes
  Security review               Partially
  Insurance/legal correctness   Human validation required
  Production approval           Human required

Do not ask the agent to build everything in one huge prompt.

## 3. One-Day Phases

``` text
Phase 1 — Foundation
        ↓
Phase 2 — RAG + Documents
        ↓
Phase 3 — Claims + Adjudication
        ↓
Phase 4 — Product UI
        ↓
Phase 5 — Docker + GitHub + Demo
```

## 4. Phase 1 --- Foundation

Use:

-   FastAPI
-   PostgreSQL
-   React/Next.js
-   Modular RAG services
-   Docker

Initial structure:

``` text
claim-sense/
├── backend/
├── frontend/
├── ai/
├── ingestion/
├── adjudication/
├── data/
├── tests/
├── docs/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── docker-compose.yml
```

Agent prompt:

> You are the lead software architect. Build the initial architecture
> for Claim Sense, an AI-powered insurance claims intelligence platform.
> Use FastAPI, PostgreSQL, React/Next.js and a modular RAG architecture.
> Create production-quality folder structure, configuration management,
> logging, error handling and Docker support. Do not implement business
> logic yet.

## 5. Phase 2 --- RAG

Build:

``` text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector / Hybrid Search
 ↓
Retriever
 ↓
LLM
 ↓
Citation
```

For a one-day prototype, a practical stack is:

-   FastAPI
-   LangChain or LlamaIndex
-   Chroma/Qdrant/pgvector
-   Embeddings
-   LLM API

For enterprise production, this can later move to Azure AI Search.

Do not spend the entire day configuring a complex cloud infrastructure.

## 6. Phase 3 --- Claim Workflow

APIs:

``` text
POST /claims
POST /claims/{id}/documents
POST /claims/{id}/analyze
GET /claims/{id}
GET /claims/{id}/decision
POST /claims/{id}/review
```

Example analysis output:

``` json
{
  "claim_id": "CLM-001",
  "status": "PARTIALLY_COVERED",
  "claimed_amount": 500000,
  "eligible_amount": 360000,
  "coverage": {
    "status": "covered",
    "confidence": 0.93
  },
  "deductible": 10000,
  "risk": {
    "level": "medium",
    "signals": [
      "High claim amount"
    ]
  },
  "missing_documents": [],
  "recommendation": "PARTIAL_APPROVAL",
  "evidence": [
    {
      "document": "health_policy.pdf",
      "page": 37,
      "section": "7.1"
    }
  ]
}
```

## 7. Phase 4 --- Product UI

The dashboard should show:

``` text
CLAIM SENSE
AI-Powered Insurance Claims Intelligence

[ Upload Claim ] [ Upload Policy ]

Claims | Pending | High Risk
```

The claim analysis screen should show:

-   Claim amount
-   Eligible amount
-   Status
-   Confidence
-   Risk
-   Coverage
-   Evidence
-   Policy citations
-   Recommendation
-   Approve / Modify / Escalate actions

This is what turns the project into a product.

## 8. Phase 5 --- GitHub and Deployment

At each major milestone:

``` bash
git add .
git commit -m "Implement RAG document processing"
git push
```

Then:

``` bash
git commit -m "Implement claim adjudication"
git push
```

Then:

``` bash
git commit -m "Add Claim Sense dashboard"
git push
```

## 9. AI Agent Prompts

### Architecture

> Build the initial architecture for Claim Sense, an AI-powered
> insurance claims intelligence platform. Use FastAPI, PostgreSQL,
> React/Next.js and modular RAG services. Create clean modules,
> configuration management, logging, error handling and Docker support.

### Policy ingestion

> Implement the policy document ingestion pipeline. Accept PDF files,
> extract text, preserve page numbers, create semantic chunks and
> metadata including document_id, policy_version, effective_date,
> section, clause and page number. Write unit tests.

### RAG

> Implement the RAG service. Use hybrid retrieval where possible.
> Retrieve relevant policy clauses and return answers with source
> document, page and section citations. The model must refuse to answer
> when sufficient evidence cannot be found.

### Claim extraction

> Implement claim document extraction. Extract claim_id, policy_id,
> claim type, incident date, claimed amount, claimant information,
> documents and relevant structured fields. Return validated Pydantic
> JSON.

### Adjudication

> Implement the insurance adjudication rules engine. Do not use the LLM
> for arithmetic. Implement coverage, exclusion, deductible, co-pay,
> sub-limit and maximum coverage rules as deterministic functions.
> Return a transparent calculation breakdown.

### Orchestration

> Implement the Claim Sense analysis orchestrator. Given a claim,
> retrieve the applicable policy version, extract claim facts, retrieve
> relevant policy clauses, execute deterministic adjudication rules,
> calculate risk signals and generate an evidence-backed recommendation.

### UI

> Build the Claim Sense enterprise dashboard using Next.js. Include
> dashboard, claims list, claim details, document upload, policy upload,
> AI analysis, evidence citations and human review actions. Make the UI
> professional and responsive.

### Security

> Add authentication-ready architecture, role-based permissions, audit
> logging, structured application logs, API error handling and security
> protections. Do not expose secrets or PII.

### Docker

> Create Docker configuration for the entire application and a local
> docker-compose environment containing frontend, backend, PostgreSQL
> and vector database. Add health checks.

### QA

> Review the entire repository as a senior software engineer. Identify
> bugs, broken imports, security issues, missing environment variables,
> incorrect API contracts, RAG grounding problems and deployment issues.
> Fix the problems and run the tests.

## 10. Important Limitation

Do not attempt all of these in one day:

-   Production fraud ML
-   Full regulatory compliance certification
-   Real insurer integration
-   Real customer PII
-   Massive production datasets
-   AKS infrastructure
-   Full mobile application
-   Multimodal damage assessment
-   Fully automated production claim approval

These belong in the roadmap.

## 11. Use Synthetic Data

If real claims are unavailable, use clearly labelled synthetic claims.

Risk signals can initially be deterministic:

``` python
if claim_amount > 500000:
    risk_signals.append("High claim amount")

if duplicate_claim:
    risk_signals.append("Potential duplicate")

if missing_documents:
    risk_signals.append("Missing documentation")
```

Later replace them with ML.

## 12. Definition of 100% MVP

  Component           Target
  ------------------- ----------
  Repository          Complete
  README              Complete
  Backend             Complete
  Frontend            Complete
  Database            Complete
  PDF ingestion       Complete
  RAG                 Complete
  Policy citations    Complete
  Claim extraction    Complete
  Coverage analysis   Complete
  Adjudication        Complete
  Risk signals        Complete
  Human review        Complete
  Dashboard           Complete
  Docker              Complete
  Tests               Complete
  GitHub              Complete
  Demo dataset        Complete

Then list enterprise features under the production roadmap.

## 13. Core Rule

> A working 5,000-line product is worth far more than a broken
> 50,000-line AI-generated project.

The workflow should be:

``` text
Build
 ↓
Run
 ↓
Test
 ↓
Fix
 ↓
Commit
 ↓
Next feature
```

The AI agent can write much of the code, but you remain responsible for
architecture, insurance logic validation and final product quality.


---

# FINAL UPDATE — 4–5 HOUR AGENTIC AI EXECUTION MODE

The current Project 1 execution objective is a 4–5 hour sprint for the final
presentation. Treat this as an aggressive MVP/product vertical-slice target,
not an enterprise-certification guarantee.

## Priority order

```text
Repository
→ Vibe source-of-truth
→ Runnable skeleton
→ Database
→ Policy ingestion
→ Agentic RAG
→ Claim extraction
→ Coverage
→ Deterministic adjudication
→ Risk/Fraud
→ Supervisor
→ Human review
→ Audit
→ Interactive UI
→ Docker
→ GitHub
→ Deploy
→ Smoke test
```

## Agentic AI roles

Use a supervisor/orchestrator with bounded logical specialist agents:

- Intake Agent
- Document Intelligence Agent
- Policy Retrieval Agent
- Coverage Agent
- Risk/Fraud Agent
- Evidence Agent
- Review/Workflow Agent
- Audit Agent

Critical financial calculations remain deterministic tools.

## 4–5 hour schedule

```text
0:00–0:30  Audit + docs
0:30–1:15  Backend + frontend + DB + Docker
1:15–2:00  Policy ingestion + RAG
2:00–2:45  Claim + extraction + coverage
2:45–3:30  Adjudication + risk + orchestration
3:30–4:15  Review + audit + UI
4:15–4:45  QA + Docker + GitHub
4:45–5:00  Deployment + smoke test
```

## Release rule

Do not spend the final deployment window implementing optional enterprise
features. Protect the complete golden path and deploy the validated build.

A feature is VERIFIED only after it has been executed and validated.
