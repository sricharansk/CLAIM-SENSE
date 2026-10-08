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


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
