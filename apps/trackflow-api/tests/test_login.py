from jose import jwt

from app.core.config import get_settings
from conftest import register_user


def test_login_valid_credentials_returns_token_with_correct_subject(client):
    register_user(client, "login@example.com", "strongpass")
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "strongpass"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "login@example.com"


def test_login_wrong_password_rejected(client):
    register_user(client, "wrong@example.com", "strongpass")
    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "badpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_rejected(client):
    response = client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "strongpass"},
    )

    assert response.status_code == 401
    # Same message as wrong-password case — must not reveal whether the email exists.
    assert response.json()["detail"] == "Invalid email or password"


def test_login_missing_password_rejected(client):
    response = client.post("/auth/login", json={"email": "login@example.com"})

    assert response.status_code == 422


def test_login_invalid_email_format_rejected(client):
    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "strongpass"},
    )

    assert response.status_code == 422
