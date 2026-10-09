# PRD — Claim Sense

**Registered title:** Claim Sense: RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant
**Positioning:** AI-Powered Insurance Claims Intelligence, Adjudication & Policy Decision-Support Platform

## Problem

Claims handlers must read policy wordings that change by version, check coverage, waiting periods and exclusions, compute payable amounts with limits and cost-sharing, spot risk, and justify every decision. Done by hand this is slow and inconsistent, and the reasoning behind a decision is often not recorded.

## What Claim Sense does

Claim Sense takes a claim and its documents and gives the reviewer:

1. the policy wording version in force on the incident date;
2. the clauses that matter, cited by version, section, clause and page;
3. coverage, waiting-period, exclusion and document checks;
4. a deterministic calculation of the payable amount;
5. transparent risk signals;
6. an evidence-backed recommendation.

A human decides, within role-based limits. Every step is audited.

## Users

| Role | Needs | In this build |
|---|---|---|
| Claims adjuster | Upload documents, see facts, evidence, coverage and calculation, decide within an approval limit | `adjuster` (limit ₹2,00,000) |
| Supervisor | Decide escalated and high-value claims, maintain policy wordings | `supervisor` |
| Manager | See pending, high-risk and escalated work, override and escalation rates | Dashboard (all roles) |
| Auditor | Trace what the system and each reviewer did | `auditor` (read-only), audit trail |

## User stories (from the blueprint) and where they are met

| Story | Met by |
|---|---|
| Upload claim documents so facts are extracted | New claim, Documents tab, `agents/document.py` |
| Retrieve the correct policy version for historical claims | Policy Retrieval Agent, evaluation cases C08, C11, C12 |
| See evidence with page/section citations | Policy & evidence tab, assistant citations |
| See a transparent calculation (deductible, co-pay, limits) | Adjudication tab waterfall, `adjudication/rules.py` |
| See pending, high-risk and escalated claims | Dashboard, Review queue |
| Trace system and reviewer activity | Audit tab, Audit trail screen |

## In scope (MVP)

Health and motor lines on synthetic data. The MVP covers:
- policy ingestion from PDF or Markdown;
- hybrid RAG with citations;
- coverage checks and deterministic adjudication;
- risk signals and recommendations;
- human review with approval limits, escalation and decision letters;
- settlement deadlines and the audit trail;
- the dashboard and the golden evaluation;
- Docker deployment and CI.

## Out of scope (this version)

- Real customer data.
- Insurer core-system integration.
- SSO.
- OCR for scanned documents.
- ML fraud models.
- Property and travel lines.
- Legal or compliance certification.

See `IMPLEMENTATION_STATUS.md` for the roadmap.

## Success measures

- **Evaluation suite:** every check in `reports/evaluation.md` passes, covering all ten blueprint case types.
- **Amounts:** every payable amount is reproducible by hand from the cited clauses.
- **AI never decides:** no adverse decision without a human note; no money computed by an LLM.
- **Golden path:** works end to end in Docker on PostgreSQL, and in the deployed environment once a cloud account is available.
