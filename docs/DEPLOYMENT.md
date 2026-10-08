# Deployment

Status: **not deployed yet.** No cloud credentials were available while building. Do not claim a deployment until `scripts/smoke_test.py <url>` passes against it.

## Local Docker

```bash
docker compose up --build        # app on http://localhost:8080, PostgreSQL in a volume
python3 scripts/smoke_test.py http://localhost:8080
docker compose down -v           # remove containers and data
```

Behind a TLS-inspecting proxy, pass its CA to the build: `docker build --secret id=ca,src=/path/to/ca.crt .`

## Option A: Azure Container Apps (blueprint target)

1. Create a resource group, an Azure Container Registry and a service principal with contributor access to the group.
2. In GitHub repository settings add the secret `AZURE_CREDENTIALS` (service principal JSON) and the variables `AZURE_RESOURCE_GROUP`, `AZURE_CONTAINERAPP_NAME`, `AZURE_ACR_NAME`, `AZURE_LOCATION`.
3. Run the **Deploy to Azure Container Apps** workflow. It builds the image, deploys it with external ingress on port 8000, and runs the smoke test against the new URL.
4. For persistent data, create Azure Database for PostgreSQL and set `DATABASE_URL=postgresql+psycopg://...` on the container app. Optionally set `ANTHROPIC_API_KEY` as a secret.

## Option B: Render (fastest demo)

1. Merge PR #1 into `main` first; Render builds the default branch.
2. On render.com choose **New → Blueprint** and select this repository; `render.yaml` defines a free Docker web service and generates `AUTH_SECRET`. Enter a `DEMO_PASSWORD` when asked (or leave it to use the default).
3. Wait for the health check on `/api/v1/health`, then run `python3 scripts/smoke_test.py https://<your-app>.onrender.com <DEMO_PASSWORD>`.

The free plan uses SQLite that is re-seeded on each restart, which suits a demo but not real data.

## Environment variables

See `.env.example`. The app reads `PORT` when the platform sets it.
