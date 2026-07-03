from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["TINYDB_PATH"] = tempfile.mktemp(suffix=".json")

from app.core.config import get_settings  # noqa: E402
from app.database import get_engine, init_db  # noqa: E402
from app.main import app  # noqa: E402

get_settings.cache_clear()
get_engine.cache_clear()


@pytest.fixture(name="client")
def client_fixture():
    init_db()
    with TestClient(app) as client:
        yield client


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "name": "Ana Whitfield",
            "email": "ana@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_me(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "name": "Carlos Vega",
            "email": "carlos@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    assert "token" in response.json()

    token = response.json()["token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "carlos@example.com"
    assert body["name"] == "Carlos Vega"


def test_inventory_flow(client: TestClient, auth_headers: dict):
    product = client.post(
        "/inventory/products",
        headers=auth_headers,
        json={
            "name": "Wireless Earbuds",
            "sku": "TF-LA-EB-001",
            "warehouse_location": "los_angeles",
            "client_brand": "SoundWave Co",
            "low_stock_threshold": 5,
        },
    )
    assert product.status_code == 201
    product_body = product.json()
    assert product_body["current_stock"] == 0
    product_id = product_body["id"]

    inbound = client.post(
        "/inventory/orders/inbound",
        headers=auth_headers,
        json={"product_id": product_id, "quantity": 20},
    )
    assert inbound.status_code == 201

    detail = client.get(f"/inventory/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["current_stock"] == 20

    outbound = client.post(
        "/inventory/orders/outbound",
        headers=auth_headers,
        json={"product_id": product_id, "quantity": 8},
    )
    assert outbound.status_code == 201
    assert client.get(f"/inventory/products/{product_id}").json()["current_stock"] == 12

    rejected = client.post(
        "/inventory/orders/outbound",
        headers=auth_headers,
        json={"product_id": product_id, "quantity": 50},
    )
    assert rejected.status_code == 400
    assert "Insufficient stock" in rejected.json()["detail"]

    orders = client.get("/inventory/orders")
    assert orders.status_code == 200
    assert len(orders.json()) == 2
    assert all("user_uuid" in order for order in orders.json())
