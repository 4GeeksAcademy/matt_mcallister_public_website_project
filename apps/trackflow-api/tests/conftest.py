import os
import sys

import pytest
from fastapi.testclient import TestClient
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import get_db
from app.main import app


@pytest.fixture
def tinydb() -> TinyDB:
    db = TinyDB(storage=MemoryStorage)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(tinydb: TinyDB) -> TestClient:
    def _override_get_db():
        try:
            yield tinydb
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_user(client, email: str, password: str = "strongpass"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login_token(client, email: str, password: str = "strongpass") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]
