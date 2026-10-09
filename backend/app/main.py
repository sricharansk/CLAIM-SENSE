"""Claim Sense API entrypoint."""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import public, router
from .auth import seed_users
from .config import settings
from .db import Base, SessionLocal, engine
from .seed import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("claimsense")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        seed_users(db)
        if settings.seed_on_startup:
            seed(db)
        else:
            from .rag import service as rag
            rag.rebuild_index(db)
    yield


app = FastAPI(title="Claim Sense API", lifespan=lifespan,
              description="RAG-Based Insurance Claims Adjudication & Policy Knowledge Assistant", version=settings.version)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                               "script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
}


@app.middleware("http")
async def correlation_id(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    response.headers.update(SECURITY_HEADERS)
    if request.url.path in ("/docs", "/redoc"):
        # Swagger UI loads its assets from a CDN; keep the other headers but skip the strict CSP there.
        del response.headers["Content-Security-Policy"]
    return response


def _error(request: Request, status: int, message, code: str, headers: dict | None = None):
    return JSONResponse(status_code=status, headers=headers, content={"error": {"code": code, "message": message,
                        "correlation_id": getattr(request.state, "correlation_id", None)}})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return _error(request, exc.status_code, exc.detail, f"HTTP_{exc.status_code}", exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    msg = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
    return _error(request, 422, msg, "VALIDATION_ERROR")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error [%s]", getattr(request.state, "correlation_id", "-"))
    return _error(request, 500, "Unexpected server error. Quote the correlation ID when reporting it.", "INTERNAL_ERROR")


app.include_router(public)
app.include_router(router)

# Serve the built frontend when present (single-container deployment).
_static = Path(__file__).resolve().parents[1] / "static"
if _static.exists():
    app.mount("/assets", StaticFiles(directory=_static / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        target = _static / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(_static / "index.html")
