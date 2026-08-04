from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from telemetry import router, storage
from telemetry.models import PROPERTY_MODELS, TelemetryEvent


INVENTORY_BASE = {
    "warehouse": "los_angeles",
    "client_id": "client_fashion_co",
    "product_id": "SKU-F-001",
    "product_category": "fashion",
    "quantity": 5,
}

VALID_PROPERTIES = {
    "inbound_order_created": {**INVENTORY_BASE, "order_id": "IN-1"},
    "outbound_order_created": {**INVENTORY_BASE, "order_id": "OUT-1"},
    "outbound_order_rejected": {**INVENTORY_BASE, "failure_reason": "insufficient stock"},
    "stock_threshold_triggered": {
        **INVENTORY_BASE,
        "threshold": 10,
        "current_stock": 5,
    },
    "direct_stock_edit_rejected": {
        **INVENTORY_BASE,
        "attempted_delta": 5,
        "reason": "stock_changes_must_go_through_orders",
    },
    "inventory_discrepancy_detected": {
        **INVENTORY_BASE,
        "system_quantity": 10,
        "counted_quantity": 5,
        "delta": -5,
    },
    "inbound_order_validation_failed": {
        **INVENTORY_BASE,
        "failure_reason": "invalid_payload",
    },
    "user_login_succeeded": {"method": "password"},
    "user_login_failed": {"failure_code": "invalid_credentials"},
    "session_expired": {
        "last_page": "/inventory",
        "session_duration_seconds": 120,
    },
    "page_viewed": {"path": "/inventory", "title": "Inventory"},
    "page_load_recorded": {"path": "/inventory", "duration_ms": 125},
    "api_latency_recorded": {
        "endpoint": "/inventory/stock",
        "method": "GET",
        "status_code": 200,
        "duration_ms": 18,
    },
    "frontend_error_uncaught": {
        "message": "render failed",
        "path": "/inventory",
        "source": "window.onerror",
    },
    "picking_duration_recorded": {
        **INVENTORY_BASE,
        "order_id": "OUT-1",
        "duration_ms": 450,
    },
    "flow_abandoned": {
        "flow_type": "outbound",
        "last_field": "quantity",
        "elapsed_seconds": 30,
    },
}


def event(event_type: str, *, timestamp: str = "2026-08-01T12:00:00Z") -> dict:
    return {
        "eventId": f"event-{event_type}",
        "timestamp": timestamp,
        "sessionId": "sess-test",
        "userId": "user-test",
        "event_type": event_type,
        "schemaVersion": "1.0.0",
        "requestId": f"request-{event_type}",
        "properties": deepcopy(VALID_PROPERTIES[event_type]),
    }


@pytest.fixture()
def client() -> TestClient:
    storage._MEMORY_EVENTS.clear()
    router._REPORT_CACHE.clear()
    app = FastAPI()
    app.include_router(router.router)
    return TestClient(app)


@pytest.mark.parametrize("event_type", sorted(PROPERTY_MODELS))
def test_every_contract_event_validates(event_type: str):
    assert TelemetryEvent.model_validate(event(event_type)).event_type == event_type


def test_event_validation_rejects_unknown_and_extra_properties():
    unknown = event("page_viewed")
    unknown["event_type"] = "credential_failed"
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(unknown)

    extra = event("page_viewed")
    extra["properties"]["email"] = "private@example.com"
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(extra)


def test_ingestion_stores_valid_events_and_rejects_invalid_individually(client: TestClient):
    invalid = event("outbound_order_created")
    invalid["properties"].pop("warehouse")

    response = client.post(
        "/telemetry/events",
        json={"events": [event("inventory_discrepancy_detected"), invalid]},
    )

    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 1, "rejected": 1}
    assert storage.memory_count() == 1


def test_report_honors_period_and_returns_runtime_metrics(client: TestClient):
    events = [
        event("user_login_succeeded"),
        event("user_login_failed"),
        event("api_latency_recorded"),
        event("inventory_discrepancy_detected"),
        event("page_viewed", timestamp="2026-07-01T12:00:00Z"),
    ]
    assert client.post("/telemetry/events", json={"events": events}).json()["stored"] == 5

    response = client.get(
        "/telemetry/report",
        params={
            "start_date": "2026-08-01T00:00:00Z",
            "end_date": "2026-08-02T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period"]["from"] == "2026-08-01T00:00:00+00:00"
    assert sum(row["count"] for row in body["metrics"]["events_per_day"]) == 4
    assert body["metrics"]["auth_failure_rate"][0]["failure_rate"] == 0.5
    latency = body["metrics"]["api_latency_by_endpoint"][0]
    assert latency["endpoint"] == "/inventory/stock"
    assert latency["request_count"] == 1


def test_report_rejects_invalid_period(client: TestClient):
    response = client.get(
        "/telemetry/report",
        params={"start_date": "2026-08-02", "end_date": "2026-08-01"},
    )
    assert response.status_code == 422
