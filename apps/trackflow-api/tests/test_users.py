from conftest import login_token, register_user


def test_users_list_requires_auth(client):
    response = client.get("/users")
    assert response.status_code == 401


def test_public_users_create_returns_user(client, tinydb):
    response = client.post(
        "/users",
        json={"name": "Public User", "email": "public@example.com", "password": "strongpass"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Public User"
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
    response = client.post(
        "/users",
        json={"name": "Duplicate User", "email": "dup@example.com", "password": "strongpass"},
    )
    assert response.status_code == 409


def test_user_can_update_name(client):
    register_user(client, "profile@example.com", name="Original Name")
    token = login_token(client, "profile@example.com")

    response = client.put(
        "/users/1",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_user_can_change_password_with_current_password(client):
    register_user(client, "password@example.com")
    token = login_token(client, "password@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    wrong = client.put(
        "/users/1/change-password",
        json={"current_password": "incorrect", "new_password": "newstrongpass"},
        headers=auth,
    )
    assert wrong.status_code == 400

    changed = client.put(
        "/users/1/change-password",
        json={"current_password": "strongpass", "new_password": "newstrongpass"},
        headers=auth,
    )
    assert changed.status_code == 204
    assert client.post(
        "/auth/login",
        json={"email": "password@example.com", "password": "strongpass"},
    ).status_code == 401
    assert client.post(
        "/auth/login",
        json={"email": "password@example.com", "password": "newstrongpass"},
    ).status_code == 200