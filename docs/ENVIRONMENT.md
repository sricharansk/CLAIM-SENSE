# Environment

Every setting the app, its containers, scripts and workflows read. Application settings are read once, at import time, by `backend/app/config.py` (`Settings`). No other backend module reads the environment directly.

## Application settings (`backend/app/config.py`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///<repo>/backend/claimsense.db` | SQLAlchemy URL. PostgreSQL uses `postgresql+psycopg://…` (`psycopg[binary]` is in `backend/requirements.txt`) |
| `CLAIMSENSE_DATA_DIR` | `<repo>/data` | Synthetic policies, claim packets, evaluation packets, portfolio, CAS benchmark and source registry |
| `CLAIMSENSE_STORAGE_DIR` | `<repo>/backend/storage` | Uploaded claim documents, one folder per claim. Created on start-up |
| `CLAIMSENSE_SEED` | `true` | Only the value `true` (any case) seeds the 7 synthetic wordings, the insured policies and the 63 scenario claims on start-up (idempotent, `backend/app/seed.py`). Any other value skips seeding and only rebuilds the retrieval index. Demo users are seeded either way |
| `CLAIMSENSE_SEED_PACKETS` | `true` | Also seeds the 9 evaluation packets as claims, under the numbers in `seeded_as` (72 claims in all). The tests, the evaluation and the claims report set it to `false` because they file the same packets through the API (D25) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Comma-separated allowed origins |
| `ANTHROPIC_API_KEY` | empty | Turns on LLM-worded assistant answers (`backend/app/llm.py`). Empty means extractive answers. Never used for amounts or decisions |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | Model name sent to the Anthropic Messages API |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Size limit for claim documents and policy wordings |
| `RAG_MIN_SCORE` | `0.15` | Minimum fused retrieval score for the assistant to answer instead of refusing |
| `AUTH_SECRET` | empty | Key that signs login tokens. When empty, a random key is generated per process and `claimsense.auth` logs a warning; tokens then stop working after a restart and differ between instances |
| `TOKEN_TTL_HOURS` | `12` | Token lifetime |
| `DEMO_PASSWORD` | `claimsense-demo` | Password for the seeded synthetic accounts `adjuster`, `supervisor`, `auditor`. Leave it unset rather than empty: an empty value is stored as the password, and sign-in rejects an empty password |
| `LOGIN_MAX_FAILURES` | `5` | Failed sign-ins per (client address, username) before sign-in returns 429 |
| `LOGIN_WINDOW_SECONDS` | `300` | Window for counting failures and length of the lock-out |

Fixed in code, not configurable: `version` `1.0.0`, `rules_version` `adjudication-rules/1.1.0`, `risk_version` `risk-rules/1.1.0` (`config.py`), and the adjuster approval limit ₹2,00,000 (`DEMO_USERS` in `backend/app/auth.py`).

`DEMO_PASSWORD` is applied only when a demo user is first created (`seed_users` in `auth.py` skips existing users). On a persistent database, changing it later does not change the stored passwords until the database is reset.

## Values by environment

| Variable | Local (`uvicorn`) | Docker Compose (`docker-compose.yml`) | Docker image default (`Dockerfile`) | Render (`render.yaml`) |
|---|---|---|---|---|
| `DATABASE_URL` | config default (SQLite in `backend/`) | `postgresql+psycopg://claimsense:${POSTGRES_PASSWORD:-claimsense-local}@db:5432/claimsense` | `sqlite:////app/var/claimsense.db` | not set, so the image's SQLite; re-seeded on each start |
| `CLAIMSENSE_STORAGE_DIR` | config default | image default, on the `uploads` volume | `/app/var/storage` | image default |
| `CLAIMSENSE_DATA_DIR` | config default | config default (`/app/data` in the image) | not set | not set |
| `CLAIMSENSE_SEED` | config default (`true`) | `"true"` | not set | `"true"` |
| `CLAIMSENSE_SEED_PACKETS` | config default (`true`) | not set (`true`) | not set | not set (`true`) |
| `AUTH_SECRET` | empty unless exported | `${AUTH_SECRET:-local-dev-only-change-me}` | not set | `generateValue: true` (Render generates one) |
| `DEMO_PASSWORD` | default unless exported | `${DEMO_PASSWORD:-claimsense-demo}` | not set | `sync: false` (asked for at set-up; empty uses the default) |
| `ANTHROPIC_API_KEY` | empty unless exported | `${ANTHROPIC_API_KEY:-}` | not set | `sync: false` |
| `PORT` | not used (`--port 8000` in the README command) | not set, so 8000 (published as host port 8080) | `${PORT:-8000}` in `CMD` | set by the platform |

The remaining application variables (`CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, `RAG_MIN_SCORE`, `TOKEN_TTL_HOURS`, `ANTHROPIC_MODEL`, `LOGIN_*`) are not set in Compose, the Dockerfile or `render.yaml`, so the config defaults apply unless the platform sets them.

## Container and platform variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `POSTGRES_PASSWORD` | `docker-compose.yml`, `.env.example` | `claimsense-local` | Password for the Compose PostgreSQL service and the app's `DATABASE_URL`. Local only |
| `POSTGRES_DB`, `POSTGRES_USER` | `docker-compose.yml` (db service) | `claimsense` | Fixed database and user names |
| `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED` | `Dockerfile` | `1` | No `.pyc` files; unbuffered logs |
| `NODE_EXTRA_CA_CERTS`, `PIP_CERT` | `Dockerfile` build steps | unset | Set only when the build is given a CA with `--secret id=ca,src=<ca.crt>` (TLS-inspecting proxies) |
| `PORT` | `Dockerfile` `CMD` | `8000` | Listening port inside the container |

## `.env` and `.env.example`

`.env.example` lists `DATABASE_URL`, `POSTGRES_PASSWORD`, `CLAIMSENSE_SEED`, `CLAIMSENSE_SEED_PACKETS`, `CLAIMSENSE_STORAGE_DIR`, `CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, `RAG_MIN_SCORE`, `AUTH_SECRET`, `TOKEN_TTL_HOURS`, `DEMO_PASSWORD`, `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`. `.env` is ignored by git.

The backend does not load a `.env` file itself (there is no dotenv call in `backend/app`). Docker Compose reads `.env` from the project directory only to fill the `${…}` references in `docker-compose.yml` (`POSTGRES_PASSWORD`, `AUTH_SECRET`, `DEMO_PASSWORD`, `ANTHROPIC_API_KEY`). For a local `uvicorn` run, export the variables in the shell (or pass `--env-file` to uvicorn).

`.env.example` does not list `CLAIMSENSE_DATA_DIR`, `LOGIN_MAX_FAILURES` or `LOGIN_WINDOW_SECONDS`.

## Frontend

The frontend reads no environment variables: there are no `VITE_*` variables or `import.meta.env` uses in `frontend/src`. The API base is the same-origin path `/api/v1` (`frontend/src/api.ts`). In development, `frontend/vite.config.ts` serves on port 5173 and proxies `/api` to `http://localhost:8000`. In the image, FastAPI serves the built UI from `backend/static`.

## Scripts, tests and browser suite

| Variable | Read by | Default | Purpose |
|---|---|---|---|
| `DEMO_PASSWORD` | `scripts/smoke_test.py` (second argument wins), `e2e/tests/golden.spec.mjs` | `claimsense-demo` | Password used to sign in |
| `BASE_URL` | `e2e/playwright.config.mjs` | `http://localhost:8080` | Target of the browser suite |
| `PW_CHROMIUM` | `e2e/playwright.config.mjs` | unset | Path to a preinstalled Chromium |
| `DATABASE_URL`, `CLAIMSENSE_STORAGE_DIR`, `CLAIMSENSE_SEED`, `CLAIMSENSE_SEED_PACKETS` | set by `backend/tests/conftest.py`, `scripts/evaluate.py` and `scripts/claims_report.py` (packets `false`); `scripts/provenance.py` sets the first two | temporary SQLite and storage | Isolate tests and reports from a developer database. All four also remove `ANTHROPIC_API_KEY` so results are deterministic |

`scripts/fetch_public_data.py` (CAS Schedule P benchmark) reads no environment variables; its options are command-line arguments (`--raw-dir`).

## GitHub Actions

| Name | Kind | Used by | Purpose |
|---|---|---|---|
| `AZURE_CREDENTIALS` | secret | `deploy-azure.yml` | Service principal JSON for `azure/login` |
| `AZURE_RESOURCE_GROUP`, `AZURE_CONTAINERAPP_NAME`, `AZURE_ACR_NAME`, `AZURE_LOCATION` | variables | `deploy-azure.yml` | Target of the Container Apps deployment |
| `DEMO_PASSWORD` | secret, optional | `deploy-azure.yml`, `verify-deployment.yml` | Password for the post-deploy smoke test; falls back to `claimsense-demo` |
| `url`, `browser_tests` | workflow inputs | `verify-deployment.yml` | Deployed URL to check; whether to run the Playwright suite |

`ci.yml` sets no secrets; the Compose stack uses its local defaults.

## Rules

- Never commit `.env` or real secrets. The Compose defaults (`claimsense-local`, `local-dev-only-change-me`) are for local use only.
- Set `AUTH_SECRET` and a non-default `DEMO_PASSWORD` on any shared deployment (`docs/SECURITY.md`).
- Use only synthetic data with any configuration.
