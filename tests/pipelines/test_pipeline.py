"""
Unit tests for TrackFlow warehouse telemetry transform tasks.

Run from monorepo root:
    python -m pytest tests/pipelines/test_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PIPELINES_DIR = Path(__file__).resolve().parents[2] / "data" / "pipelines"
sys.path.insert(0, str(PIPELINES_DIR))

from pipeline import transform_warehouse_shipment_kpis  # noqa: E402


def _outbound(
    *,
    event_id: str,
    timestamp: str,
    warehouse: str,
    brand: str,
    quantity: int,
    sku: str = "TF-LA-EB-001",
) -> dict:
    return {
        "eventId": event_id,
        "timestamp": timestamp,
        "sessionId": "sess-test",
        "userId": "usr_test",
        "event_type": "outbound_order_created",
        "schemaVersion": "1.0.0",
        "requestId": f"req-{event_id}",
        "properties": {
            "order_id": 1,
            "product_id": 1,
            "sku": sku,
            "quantity": quantity,
            "warehouse_location": warehouse,
            "client_brand": brand,
        },
    }


def test_transform_aggregates_outbound_by_warehouse_and_brand():
    events = [
        _outbound(
            event_id="a",
            timestamp="2026-07-10T10:00:00.000Z",
            warehouse="los_angeles",
            brand="AcmeApparel",
            quantity=10,
        ),
        _outbound(
            event_id="b",
            timestamp="2026-07-10T12:00:00.000Z",
            warehouse="los_angeles",
            brand="AcmeApparel",
            quantity=5,
        ),
        _outbound(
            event_id="c",
            timestamp="2026-07-10T14:00:00.000Z",
            warehouse="zaragoza",
            brand="IberiaCosmetics",
            quantity=20,
        ),
    ]

    result = transform_warehouse_shipment_kpis.fn(events)

    assert len(result) == 2
    la = next(r for r in result if r["warehouse_location"] == "los_angeles")
    zg = next(r for r in result if r["warehouse_location"] == "zaragoza")
    assert la["outbound_order_count"] == 2
    assert la["outbound_unit_quantity"] == 15
    assert la["client_brand"] == "AcmeApparel"
    assert zg["outbound_order_count"] == 1
    assert zg["outbound_unit_quantity"] == 20


def test_transform_includes_inbound_and_product_created_counts():
    events = [
        {
            "eventId": "in-1",
            "timestamp": "2026-07-10T08:00:00.000Z",
            "event_type": "inbound_order_created",
            "properties": {
                "order_id": 1,
                "product_id": 1,
                "sku": "TF-ZG-CS-010",
                "quantity": 50,
                "warehouse_location": "zaragoza",
                "client_brand": "IberiaCosmetics",
            },
        },
        {
            "eventId": "prod-1",
            "timestamp": "2026-07-10T09:00:00.000Z",
            "event_type": "product_created",
            "properties": {
                "product_id": 1,
                "sku": "TF-ZG-CS-010",
                "warehouse_location": "zaragoza",
                "client_brand": "IberiaCosmetics",
                "low_stock_threshold": 10,
            },
        },
        _outbound(
            event_id="out-1",
            timestamp="2026-07-10T11:00:00.000Z",
            warehouse="zaragoza",
            brand="IberiaCosmetics",
            quantity=3,
            sku="TF-ZG-CS-010",
        ),
    ]

    result = transform_warehouse_shipment_kpis.fn(events)
    assert len(result) == 1
    row = result[0]
    assert row["inbound_order_count"] == 1
    assert row["inbound_unit_quantity"] == 50
    assert row["product_created_count"] == 1
    assert row["outbound_order_count"] == 1
    assert row["outbound_unit_quantity"] == 3


def test_transform_splits_metrics_by_business_date():
    events = [
        _outbound(
            event_id="d1",
            timestamp="2026-07-10T23:00:00.000Z",
            warehouse="los_angeles",
            brand="NovaElectronics",
            quantity=2,
        ),
        _outbound(
            event_id="d2",
            timestamp="2026-07-11T01:00:00.000Z",
            warehouse="los_angeles",
            brand="NovaElectronics",
            quantity=4,
        ),
    ]

    result = transform_warehouse_shipment_kpis.fn(events)
    assert {r["metric_date"] for r in result} == {"2026-07-10", "2026-07-11"}
    by_date = {r["metric_date"]: r for r in result}
    assert by_date["2026-07-10"]["outbound_unit_quantity"] == 2
    assert by_date["2026-07-11"]["outbound_unit_quantity"] == 4


@pytest.mark.parametrize(
    "bad_event",
    [
        # null properties where a dict is expected
        {
            "eventId": "bad-null-props",
            "timestamp": "2026-07-10T10:00:00.000Z",
            "event_type": "outbound_order_created",
            "properties": None,
        },
        # incorrect warehouse type / value
        {
            "eventId": "bad-warehouse",
            "timestamp": "2026-07-10T10:00:00.000Z",
            "event_type": "outbound_order_created",
            "properties": {
                "quantity": 1,
                "warehouse_location": "miami",
                "client_brand": "AcmeApparel",
            },
        },
        # incorrect quantity type
        {
            "eventId": "bad-qty",
            "timestamp": "2026-07-10T10:00:00.000Z",
            "event_type": "outbound_order_created",
            "properties": {
                "quantity": "twelve",
                "warehouse_location": "los_angeles",
                "client_brand": "AcmeApparel",
            },
        },
        # missing timestamp
        {
            "eventId": "bad-ts",
            "timestamp": None,
            "event_type": "outbound_order_created",
            "properties": {
                "quantity": 1,
                "warehouse_location": "los_angeles",
                "client_brand": "AcmeApparel",
            },
        },
    ],
)
def test_transform_skips_malformed_events(bad_event):
    good = _outbound(
        event_id="good",
        timestamp="2026-07-10T10:00:00.000Z",
        warehouse="los_angeles",
        brand="AcmeApparel",
        quantity=7,
    )
    result = transform_warehouse_shipment_kpis.fn([bad_event, good])
    assert len(result) == 1
    assert result[0]["outbound_unit_quantity"] == 7


def test_transform_empty_input_returns_empty_list():
    assert transform_warehouse_shipment_kpis.fn([]) == []
