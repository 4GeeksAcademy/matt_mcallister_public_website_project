"""
Unit tests for TrackFlow weekly warehouse/client KPI transform tasks.

Run from monorepo root:
    python -m pytest tests/pipelines/test_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PIPELINES_DIR = Path(__file__).resolve().parents[2] / "data" / "pipelines"
sys.path.insert(0, str(PIPELINES_DIR))

from pipeline import (  # noqa: E402
    assemble_weekly_warehouse_client_rows,
    compute_discrepancy_rate,
    compute_inbound_units_count,
    compute_outbound_orders_count,
    compute_stockout_events_count,
    normalize_event,
)


def _event(
    *,
    event_type: str,
    warehouse: str,
    client_id: str,
    quantity: float = 1,
    timestamp: str = "2026-07-08T12:00:00.000Z",
) -> dict:
    raw = {
        "eventId": "test-id",
        "timestamp": timestamp,
        "sessionId": "sess-test",
        "userId": "usr_test",
        "event_type": event_type,
        "schemaVersion": "1.0.0",
        "requestId": "req-test",
        "properties": {
            "warehouse": warehouse,
            "client_id": client_id,
            "product_id": "sku-1",
            "product_category": "fashion",
            "quantity": quantity,
        },
    }
    normalized = normalize_event(raw)
    assert normalized is not None
    return normalized


def test_compute_inbound_units_count_sums_quantities_per_client():
    events = [
        _event(
            event_type="inbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=2000,
        ),
        _event(
            event_type="inbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=2200,
        ),
        _event(
            event_type="inbound_order_created",
            warehouse="zaragoza",
            client_id="electronics-es",
            quantity=800,
        ),
        _event(
            event_type="outbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=10,
        ),
    ]

    result = compute_inbound_units_count.fn(events)

    assert result["los_angeles::fashion-co"] == 4200
    assert result["zaragoza::electronics-es"] == 800
    assert "los_angeles::fashion-co" in result


def test_compute_outbound_orders_count_counts_events_not_units():
    events = [
        _event(
            event_type="outbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=10,
        ),
        _event(
            event_type="outbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=12,
        ),
        _event(
            event_type="outbound_order_created",
            warehouse="zaragoza",
            client_id="electronics-es",
            quantity=5,
        ),
    ]

    result = compute_outbound_orders_count.fn(events)

    assert result["los_angeles::fashion-co"] == 2
    assert result["zaragoza::electronics-es"] == 1


def test_compute_stockout_events_count_per_warehouse_client():
    events = [
        _event(
            event_type="stock_threshold_triggered",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=4,
        ),
        _event(
            event_type="stock_threshold_triggered",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=2,
        ),
        _event(
            event_type="inbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=100,
        ),
    ]

    result = compute_stockout_events_count.fn(events)

    assert result["los_angeles::fashion-co"] == 2


def test_discrepancy_rate_matches_hand_calculated_definition():
    """Hand-calc: 1 discrepancy / 2 outbound orders => 0.5 for fashion-co."""
    events = [
        _event(
            event_type="outbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
        ),
        _event(
            event_type="outbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
        ),
        _event(
            event_type="inventory_discrepancy_detected",
            warehouse="los_angeles",
            client_id="fashion-co",
        ),
        # zaragoza: discrepancy with zero outbound => rate 0
        _event(
            event_type="inventory_discrepancy_detected",
            warehouse="zaragoza",
            client_id="electronics-es",
        ),
    ]
    outbound = compute_outbound_orders_count.fn(events)
    result = compute_discrepancy_rate.fn(events, outbound)

    assert outbound["los_angeles::fashion-co"] == 2
    assert result["los_angeles::fashion-co"]["discrepancy_events_count"] == 1
    assert result["los_angeles::fashion-co"]["discrepancy_rate"] == pytest.approx(0.5)
    assert result["zaragoza::electronics-es"]["discrepancy_events_count"] == 1
    assert result["zaragoza::electronics-es"]["discrepancy_rate"] == 0.0


def test_compute_inbound_units_count_defensive_against_malformed_input():
    """Null / wrong-type inputs must not raise; invalid rows are skipped."""
    events = [
        None,
        "not-a-dict",
        {"event_type": "inbound_order_created"},  # missing warehouse/client
        {
            "event_type": "inbound_order_created",
            "warehouse": "los_angeles",
            "client_id": "fashion-co",
            "quantity": "not-a-number",
        },
        _event(
            event_type="inbound_order_created",
            warehouse="los_angeles",
            client_id="fashion-co",
            quantity=100,
        ),
    ]

    result = compute_inbound_units_count.fn(events)

    assert result == {"los_angeles::fashion-co": 100}


def test_assemble_weekly_warehouse_client_rows_never_crosses_clients():
    inbound = {"los_angeles::fashion-co": 4200, "zaragoza::electronics-es": 800}
    outbound = {"los_angeles::fashion-co": 2, "zaragoza::electronics-es": 2}
    stockouts = {"los_angeles::fashion-co": 2}
    discrepancies = {
        "los_angeles::fashion-co": {
            "discrepancy_events_count": 1,
            "discrepancy_rate": 0.5,
        },
        "zaragoza::electronics-es": {
            "discrepancy_events_count": 1,
            "discrepancy_rate": 0.5,
        },
    }

    rows = assemble_weekly_warehouse_client_rows.fn(
        "2026-07-07",
        inbound,
        outbound,
        stockouts,
        discrepancies,
    )

    assert len(rows) == 2
    fashion = next(r for r in rows if r["client_id"] == "fashion-co")
    electronics = next(r for r in rows if r["client_id"] == "electronics-es")
    assert fashion["inbound_units_count"] == 4200
    assert fashion["warehouse"] == "los_angeles"
    assert electronics["inbound_units_count"] == 800
    assert electronics["warehouse"] == "zaragoza"
