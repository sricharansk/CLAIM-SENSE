# syntax=docker/dockerfile:1
# Single-container build: React UI is compiled and served by the FastAPI app.
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
# Optional: behind a TLS-inspecting proxy, pass its CA with --secret id=ca,src=<ca.crt>
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/var/claimsense.db \
    CLAIMSENSE_STORAGE_DIR=/app/var/storage
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY data data
COPY --from=web /web/dist backend/static
RUN useradd --create-home claimsense && mkdir -p /app/var/storage && chown -R claimsense /app/var
USER claimsense
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
