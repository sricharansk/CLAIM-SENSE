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
    rules_version = "adjudication-rules/1.0.0"
    risk_version = "risk-rules/1.0.0"


settings = Settings()
