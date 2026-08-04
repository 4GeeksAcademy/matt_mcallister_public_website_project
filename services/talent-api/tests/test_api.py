from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    previous = os.environ.get("TALENT_DB_PATH")
    os.environ["TALENT_DB_PATH"] = str(tmp_path / "talent.json")
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            os.environ.pop("TALENT_DB_PATH", None)
        else:
            os.environ["TALENT_DB_PATH"] = previous


def candidate_payload(email: str = "ana@example.com") -> dict:
    return {
        "full_name": "Ana Whitfield",
        "email": email,
        "phone": "+1 555 0100",
        "position": "Operations Manager",
        "experience_years": 7,
        "linkedin_url": None,
        "cv_url": None,
    }


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_candidate_crud_filtering_and_pagination(client: TestClient) -> None:
    created = client.post(
        "/tracker/api/v1/records", json=candidate_payload()
    )
    assert created.status_code == 201
    candidate = created.json()
    assert candidate["status"] == "received"
    assert candidate["stage"] == "pending"
    assert candidate["notes_count"] == 0

    client.post(
        "/tracker/api/v1/records",
        json=candidate_payload("other@example.com")
        | {"full_name": "Carlos Vega", "position": "Engineer"},
    )

    listing = client.get(
        "/tracker/api/v1/records",
        params={"search": "operations", "page": 1, "limit": 1},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["data"][0]["id"] == candidate["id"]

    patched = client.patch(
        f"/tracker/api/v1/records/{candidate['id']}",
        json={"status": "in_progress", "stage": "review"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "in_progress"
    assert patched.json()["stage"] == "review"

    status_listing = client.get(
        "/tracker/api/v1/records",
        params={"status": "in_progress", "stage": "review"},
    )
    assert status_listing.status_code == 200
    assert status_listing.json()["total"] == 1
    assert status_listing.json()["data"][0]["id"] == candidate["id"]

    replacement = candidate_payload() | {"position": "Senior Operations Manager"}
    replaced = client.put(
        f"/tracker/api/v1/records/{candidate['id']}", json=replacement
    )
    assert replaced.status_code == 200
    assert replaced.json()["position"] == "Senior Operations Manager"
    assert replaced.json()["status"] == "in_progress"
    assert replaced.json()["stage"] == "review"

    deleted = client.delete(f"/tracker/api/v1/records/{candidate['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/tracker/api/v1/records/{candidate['id']}").status_code == 404


def test_notes_crud_updates_candidate_count(client: TestClient) -> None:
    candidate = client.post(
        "/tracker/api/v1/records", json=candidate_payload()
    ).json()

    created = client.post(
        f"/tracker/api/v1/records/{candidate['id']}/notes",
        json={"content": "Strong logistics background"},
    )
    assert created.status_code == 201
    note = created.json()

    notes = client.get(
        f"/tracker/api/v1/records/{candidate['id']}/notes"
    )
    assert notes.status_code == 200
    assert notes.json()[0]["content"] == "Strong logistics background"
    assert (
        client.get(f"/tracker/api/v1/records/{candidate['id']}").json()[
            "notes_count"
        ]
        == 1
    )

    deleted = client.delete(
        f"/tracker/api/v1/records/{candidate['id']}/notes/{note['id']}"
    )
    assert deleted.status_code == 204


def test_validation_and_conflicts(client: TestClient) -> None:
    assert client.post("/tracker/api/v1/records", json=candidate_payload()).status_code == 201
    assert client.post("/tracker/api/v1/records", json=candidate_payload()).status_code == 409
    assert (
        client.post(
            "/tracker/api/v1/records",
            json=candidate_payload("not-an-email"),
        ).status_code
        == 422
    )
