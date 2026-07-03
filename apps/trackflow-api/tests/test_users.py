from conftest import login_token, register_user


def test_users_list_requires_auth(client):
    response = client.get("/users")
    assert response.status_code == 401


def test_public_users_create_returns_user(client, tinydb):
    response = client.post("/users", json={"email": "public@example.com", "password": "strongpass"})
    assert response.status_code == 201
    assert response.json()["email"] == "public@example.com"
    stored = tinydb.table("users").get(doc_id=1)
    assert stored["hashed_password"] != "strongpass"


def test_user_cannot_update_another_user(client):
    register_user(client, "owner1@example.com")
    register_user(client, "owner2@example.com")

    token = login_token(client, "owner1@example.com")
    response = client.put(
        "/users/2",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_user_can_update_self(client):
    register_user(client, "self@example.com")
    token = login_token(client, "self@example.com")
    response = client.put(
        "/users/1",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_duplicate_email_conflict(client):
    register_user(client, "dup@example.com")
    response = client.post("/users", json={"email": "dup@example.com", "password": "strongpass"})
    assert response.status_code == 409