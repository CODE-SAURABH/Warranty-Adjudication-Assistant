from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_ROOT = Path(tempfile.mkdtemp(prefix="warranty-be-tests-"))
os.environ["DB_BACKEND"] = "local"
os.environ["DATABASE_URL"] = ""
os.environ["LOCAL_DB_PATH"] = str(TEST_ROOT / "test.db")
os.environ["DB_AUTO_CREATE_SCHEMA"] = "true"
os.environ["DB_SEED_ON_STARTUP"] = "true"
os.environ["POLICY_UPLOAD_DIR"] = str(TEST_ROOT / "policy_corpus")
os.environ["POLICY_MAX_UPLOAD_MB"] = "5"

from app.db import ensure_database_ready
from app.main import app


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def test_root() -> Path:
    return TEST_ROOT


@pytest.fixture(scope="session", autouse=True)
def prepared_database() -> None:
    ensure_database_ready()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
