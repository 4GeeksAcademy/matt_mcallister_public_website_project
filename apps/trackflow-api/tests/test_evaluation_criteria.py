from conftest import login_token, register_user


def test_health_route_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_crud_end_to_end_is_reachable(client):
    register_response = register_user(client, "crud@example.com")
    assert register_response.status_code == 201

    token = login_token(client, "crud@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    get_list = client.get("/users", headers=auth)
    assert get_list.status_code == 200
    assert len(get_list.json()) == 1

    get_one = client.get("/users/1", headers=auth)
    assert get_one.status_code == 200
    assert get_one.json()["email"] == "crud@example.com"

    update = client.put("/users/1", json={"name": "Crud User"}, headers=auth)
    assert update.status_code == 200
    assert update.json()["name"] == "Crud User"

    delete = client.delete("/users/1", headers=auth)
    assert delete.status_code == 204


def test_inactive_users_cannot_use_authenticated_routes(client):
    register_user(client, "inactive-crud@example.com")
    token = login_token(client, "inactive-crud@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    update = client.put("/users/1", json={"is_active": False}, headers=auth)
    assert update.status_code == 200
    assert update.json()["is_active"] is False

    assert client.get("/auth/me", headers=auth).status_code == 401
    assert client.delete("/users/1", headers=auth).status_code == 401


def test_protected_routes_return_401_without_valid_token(client):
    assert client.get("/users").status_code == 401
    assert client.get("/users/1").status_code == 401
    assert client.put("/users/1", json={"is_active": False}).status_code == 401
    assert client.delete("/users/1").status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_auth_and_users_route_structure(client):
    assert client.post("/auth/login", json={"email": "x@example.com", "password": "bad"}).status_code in [401, 422]
    assert client.post(
        "/users",
        json={
            "name": "Prefix User",
            "email": "prefix@example.com",
            "password": "strongpass",
        },
    ).status_code == 201

    assert client.get("/user").status_code == 404
    assert client.get("/authentication/me").status_code == 404


def test_secret_and_expiry_are_loaded_from_environment(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SECRET_KEY", "env-secret-key")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "99")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.secret_key == "env-secret-key"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 99

    get_settings.cache_clear()
