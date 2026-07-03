from datetime import timedelta

from app.core.security import create_access_token
from conftest import login_token, register_user


def test_me_valid_token_returns_current_user(client):
    register_user(client, "me@example.com")
    token = login_token(client, "me@example.com")

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_me_expired_token_rejected(client):
    register_user(client, "expired@example.com")
    expired_token = create_access_token("expired@example.com", expires_delta=timedelta(minutes=-1))

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401


def test_me_token_for_deleted_user_rejected(client):
    register_user(client, "deleted@example.com")
    token = login_token(client, "deleted@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    delete_response = client.delete("/users/1", headers=auth)
    assert delete_response.status_code == 204

    # Token is still cryptographically valid, but the user record is gone —
    # get_current_user must reject the request rather than return a stale identity.
    response = client.get("/auth/me", headers=auth)
    assert response.status_code == 401


def test_me_without_token_rejected(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_malformed_token_rejected(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401
