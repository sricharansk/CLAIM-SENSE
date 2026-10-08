import os
import sys
import tempfile
from pathlib import Path

import pytest

_tmp = Path(tempfile.mkdtemp(prefix="claimsense-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp / 'test.db'}"
os.environ["CLAIMSENSE_STORAGE_DIR"] = str(_tmp / "storage")
os.environ["CLAIMSENSE_SEED"] = "true"
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import REPO_ROOT  # noqa: E402
from app.main import app  # noqa: E402

DATA = REPO_ROOT / "data"


def login(c: TestClient, username: str) -> dict:
    r = c.post("/api/v1/auth/login", json={"username": username, "password": "claimsense-demo"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def new_claim(c: TestClient, folder: str, policy_number: str, claim_type: str, claimant: str) -> str:
    """Create a fresh claim from a packet in data/claims/<folder> and analyse it (as the supervisor)."""
    n = c.post("/api/v1/claims", json={"policy_number": policy_number, "claim_type": claim_type,
                                        "claimant_name": claimant}).json()["claim_number"]
    files = [("files", (p.name, p.read_bytes(), "text/plain")) for p in sorted((DATA / "claims" / folder).glob("*.txt"))]
    assert c.post(f"/api/v1/claims/{n}/documents", files=files).status_code == 201
    assert c.post(f"/api/v1/claims/{n}/analyze").json()["status"] == "SUCCEEDED"
    return n


@pytest.fixture(scope="session")
def client():
    """Signed in as the supervisor by default; pass headers=login(client, ...) to act as another user."""
    with TestClient(app) as c:
        c.headers.update(login(c, "supervisor"))
        yield c
