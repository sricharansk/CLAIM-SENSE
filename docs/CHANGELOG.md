# Changelog

Implementation history of Claim Sense by release, in the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) style. Each release has its full notes in [`RELEASE_NOTES.md`](../RELEASE_NOTES.md) and its pull requests in the timeline in [`CLAUDE.md`](../CLAUDE.md). The repository has no git tags; releases are named in the release notes. The API reports `version` `1.0.0` from `backend/app/config.py`; the rules and risk versions are reported with every analysis.

## [1.5.0] - 2026-10-30

### Added
- Personal accident and life lines: PA-SECURE and LIFE-TERM 2025.1 wordings, the benefit-schedule model (`rules.adjudicate_benefits`), accident-only cover, the 12-month suicide exclusion and the life contestable period (D27–D29).
- 13 seeded claims and 2 evaluation packets on the new lines; golden cases C58–C72 and questions Q27–Q30 (986 checks).
- A 10,000-claim synthetic portfolio across six lines.
- CAS Schedule P industry benchmark: `scripts/fetch_public_data.py`, `data/public/cas_schedule_p/benchmark.json`, `GET /api/v1/benchmarks/industry`, Data sources panel (D30).
- `docs/API.md`, `ENVIRONMENT.md`, `ERROR_HANDLING.md`, `OBSERVABILITY.md`, `UX_FLOWS.md`, `ROADMAP.md` and this changelog.

### Changed
- `adjudication-rules/1.1.0` and `risk-rules/1.1.0`.
- The policy assistant needs two specific question terms in a clause before answering a multi-term question (D31).
- The smoke test and browser tests file a personal accident and a life claim.

## [1.4.3] - 2026-10-30
### Added
- Windows and VS Code setup guide (`docs/LOCAL_SETUP.md`) and VS Code tasks.
### Security
- pypdf 6.19.0 → 6.21.2.

## [1.4.2] - 2026-10-15
### Added
- Project handover in `CLAUDE.md`; dashboard source and data in `docs/dashboard/`; presentation build script.

## [1.4.1] - 2026-10-13
### Added
- Review III presentation. Live deployment verified.

## [1.4.0] - 2026-10-12
### Added
- 16 more seeded claims (50 in all) and golden cases C42–C57; live claims report (`claims_report.py --live`).
### Changed
- A loss outside the policy period cites the coverage clause (D26).

## [1.3.1] - 2026-10-12
### Changed
- The live app seeds the evaluation packets as claims (D25).

## [1.3.0] to [1.1.0] - 2026-10-12
### Added
- 1.1.0: property (home) and travel lines. 1.2.0: the verified Render deployment. 1.3.0: every exclusion, waiting period and limit in the wordings exercised by a seeded claim. See `RELEASE_NOTES.md`.

## [1.0.0] - 2026-10-09
### Added
- The MVP golden path: agents, hybrid RAG, the `Decimal` rules engine, sign-in with roles and approval limits, human review and workflow, audit, letters, settlement clock, golden evaluation, data provenance, Docker, CI and the Render deployment.
