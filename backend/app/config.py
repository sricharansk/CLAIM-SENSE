"""Runtime configuration, read from environment variables (see .env.example)."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    app_name = "Claim Sense"
    version = "1.0.0"
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{REPO_ROOT / 'backend' / 'claimsense.db'}")
    data_dir = Path(os.getenv("CLAIMSENSE_DATA_DIR", REPO_ROOT / "data"))
    storage_dir = Path(os.getenv("CLAIMSENSE_STORAGE_DIR", REPO_ROOT / "backend" / "storage"))
    seed_on_startup = os.getenv("CLAIMSENSE_SEED", "true").lower() == "true"
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
    # Optional LLM narrative. Without a key, explanations are extractive (quoted policy text only).
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    rag_min_score = float(os.getenv("RAG_MIN_SCORE", "0.15"))
    # Signing key for login tokens. Set AUTH_SECRET in any shared deployment; without it a random
    # key is generated per process and sign-ins do not survive a restart.
    auth_secret = os.getenv("AUTH_SECRET", "")
    token_ttl_hours = int(os.getenv("TOKEN_TTL_HOURS", "12"))
    # Password for the seeded synthetic demo accounts (adjuster, supervisor, auditor).
    demo_password = os.getenv("DEMO_PASSWORD", "claimsense-demo")
    # Sign-in throttle: this many failed attempts for one username from one address locks it for the window.
    login_max_failures = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
    login_window_seconds = int(os.getenv("LOGIN_WINDOW_SECONDS", "300"))
    rules_version = "adjudication-rules/1.0.0"
    risk_version = "risk-rules/1.0.0"


settings = Settings()
