from jose import jwt

from app.core.config import get_settings
from conftest import register_user


def test_register_valid_credentials_creates_user_and_returns_token(client, tinydb):
    response = register_user(client, "user1@example.com", "strongpass")

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"

    stored = tinydb.table("users").get(doc_id=1)
    assert stored is not None
    assert stored["email"] == "user1@example.com"
    assert stored["hashed_password"] != "strongpass"

    settings = get_settings()
    payload = jwt.decode(body["access_token"], settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "user1@example.com"


def test_register_duplicate_email_returns_conflict(client, tinydb):
    register_user(client, "dup@example.com")
    response = register_user(client, "dup@example.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"
    # Business rule: only one row should exist — registration must not overwrite silently.
    assert len(tinydb.table("users")) == 1


def test_register_minimum_length_password_succeeds(client, tinydb):
    response = register_user(client, "min@example.com", "12345678")

    assert response.status_code == 201
    assert tinydb.table("users").get(doc_id=1)["email"] == "min@example.com"


def test_register_short_password_rejected(client, tinydb):
    response = register_user(client, "short@example.com", "short")

    assert response.status_code == 422
    assert len(tinydb.table("users")) == 0


def test_register_invalid_email_rejected(client, tinydb):
    response = register_user(client, "not-an-email", "strongpass")

    assert response.status_code == 422
    assert len(tinydb.table("users")) == 0
