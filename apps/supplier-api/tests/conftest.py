import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_db(tmp_path: Path):
    db_path = tmp_path / "test_suppliers.json"
    previous = os.environ.get("SUPPLIERS_DB_PATH")
    os.environ["SUPPLIERS_DB_PATH"] = str(db_path)
    try:
        yield db_path
    finally:
        if previous is None:
            os.environ.pop("SUPPLIERS_DB_PATH", None)
        else:
            os.environ["SUPPLIERS_DB_PATH"] = previous


@pytest.fixture
def client(isolated_db):
    from app.main import app

    return TestClient(app)
