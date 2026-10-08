# Security

## Controls in this build

| Area | Control | Where |
|---|---|---|
| Authentication | Sign-in required for every API route except health, readiness and login; PBKDF2-SHA256 password hashes; HMAC-SHA256 signed tokens with expiry (`AUTH_SECRET`, `TOKEN_TTL_HOURS`); failed and successful logins audited | `auth.py` |
| Authorisation | Roles: Adjuster (approval limit ₹2,00,000), Supervisor (no limit, escalations, policy ingestion), Auditor (read-only); enforced on the server; decisions recorded under the signed-in user | `auth.py`, `api/routes.py` |
| Uploads | Allow-list of `.pdf`, `.txt`, `.md`; 10 MB limit (`MAX_UPLOAD_BYTES`); empty files rejected; filename reduced to its base name; stored under a hash-prefixed name | `services.add_document` |
| Untrusted content | Document and policy text is parsed as data, never executed or used as instructions; the optional LLM prompt marks clause text as data | `agents/document.py`, `llm.py` |
| Money | Deterministic `Decimal` rules; the LLM never computes amounts | `adjudication/rules.py` |
| Decisions | AI only recommends; adverse human actions require notes; overrides are audited | `agents/review.py` |
| Audit | Append-only events with actor and correlation ID | `audit_events` |
| Errors | Uniform error body with correlation ID; no stack traces to clients | `main.py` |
| HTTP headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, strict CSP (except `/docs`) | `main.py` |
| CORS | Explicit origin list (`CORS_ORIGINS`) | `config.py` |
| SQL | SQLAlchemy ORM, no string-built SQL | all |
| Secrets | None in the repo; `.env` ignored; Compose password is a local-only default; container runs as a non-root user | `.gitignore`, `Dockerfile` |
| Data | Synthetic only; no real customer data or confidential wording | `data/` |
| Dependencies | `pip-audit` and `npm audit` run in CI | `.github/workflows/ci.yml` |

## Dependency audit (2026-10-08)

- `pip-audit -r backend/requirements.txt`: no known vulnerabilities (after upgrading FastAPI/Starlette and pypdf).
- `npm audit`: 0 vulnerabilities (after upgrading Vite to 6.4.4 and React Router to 7.18.4).

## Known gaps

- Demo accounts share one password (`DEMO_PASSWORD`); there is no user management, SSO or password reset yet. Change `DEMO_PASSWORD` and set `AUTH_SECRET` before sharing a deployment, and never use it with real data.
- Tokens are kept in the browser's local storage; there is no server-side revocation.
- No rate limiting or malware scanning on uploads.
- SQLite in single-container deployments is not suitable for concurrent production use; use PostgreSQL.
