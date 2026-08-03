"""
TrackFlow warehouse fulfillment telemetry ETL (Prefect).

Nightly pipeline: extract outbound/inbound/product events -> aggregate warehouse KPIs
-> idempotent load into daily_warehouse_kpis + pipeline_run_log.

Run from monorepo root:
    python data/pipelines/pipeline.py

Schedule: nightly ~06:00 UTC (see PIPELINE_DESIGN.md).
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from prefect import flow, task
from prefect.tasks import task_input_hash

# Monorepo paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS_PATH = REPO_ROOT / "data" / "raw" / "telemetry_events.jsonl"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "process" / "warehouse_kpis.db"

FULFILLMENT_EVENT_TYPES = frozenset(
    {
        "outbound_order_created",
        "inbound_order_created",
        "product_created",
    }
)
VALID_WAREHOUSES = frozenset({"los_angeles", "zaragoza"})


def _utcnow():
    return datetime.now(timezone.utc)


def _ensure_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS daily_warehouse_kpis (
            metric_date TEXT NOT NULL,
            warehouse_location TEXT NOT NULL,
            client_brand TEXT NOT NULL,
            outbound_order_count INTEGER NOT NULL DEFAULT 0,
            outbound_unit_quantity INTEGER NOT NULL DEFAULT 0,
            inbound_order_count INTEGER NOT NULL DEFAULT 0,
            inbound_unit_quantity INTEGER NOT NULL DEFAULT 0,
            product_created_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (metric_date, warehouse_location, client_brand)
        );

        CREATE TABLE IF NOT EXISTS pipeline_run_log (
            id TEXT PRIMARY KEY,
            flow_run_id TEXT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            records_processed INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error_message TEXT
        );
        """
    )
    conn.commit()


def get_latest_pipeline_run(db_path=None):
    # type: (Optional[Union[Path, str]]) -> Optional[Dict[str, Any]]
    """Return the most recent pipeline_run_log row, or None."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not path.exists():
        return None
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT id, flow_run_id, started_at, finished_at,
                   records_processed, status, error_message
            FROM pipeline_run_log
            ORDER BY started_at DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@task(
    name="extract_outbound_order_events",
    retries=3,
    # File / future DB IO can flake; 3 retries with 5s backoff balances resilience vs wait time.
    retry_delay_seconds=5,
)
def extract_outbound_order_events(events_path):
    # type: (str) -> List[Dict[str, Any]]
    """Load JSONL telemetry; keep fulfillment types; drop duplicate eventIds."""
    path = Path(events_path)
    if not path.exists():
        raise FileNotFoundError("Telemetry source not found: {}".format(path))

    seen = set()  # type: set
    events = []  # type: List[Dict[str, Any]]
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "Malformed JSON at line {}: {}".format(line_no, exc)
                ) from exc

            event_type = payload.get("event_type")
            if event_type not in FULFILLMENT_EVENT_TYPES:
                continue

            event_id = payload.get("eventId")
            if not event_id or event_id in seen:
                continue
            seen.add(event_id)
            events.append(payload)

    return events


@task(
    name="transform_warehouse_shipment_kpis",
    # Cache key = hash of task inputs (the events list). Expiration = 1 hour so
    # identical transforms within a nightly window skip expensive Pandas recompute.
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def transform_warehouse_shipment_kpis(events):
    # type: (List[Dict[str, Any]]) -> List[Dict[str, Any]]
    """
    Aggregate fulfillment events into daily KPI rows.

    Defensive: skips rows missing warehouse_location / client_brand / timestamp;
    rejects unknown warehouse codes and non-numeric quantities.
    """
    if not events:
        return []

    rows = []  # type: List[Dict[str, Any]]
    for event in events:
        props = event.get("properties")
        if not isinstance(props, dict):
            continue

        warehouse = props.get("warehouse_location")
        brand = props.get("client_brand")
        timestamp = event.get("timestamp")
        event_type = event.get("event_type")

        if not isinstance(timestamp, str) or not timestamp:
            continue
        if warehouse not in VALID_WAREHOUSES:
            continue
        if not isinstance(brand, str) or not brand:
            continue
        if event_type not in FULFILLMENT_EVENT_TYPES:
            continue

        quantity = props.get("quantity", 0)
        if event_type == "product_created":
            quantity = 0
        elif not isinstance(quantity, (int, float)) or quantity < 0:
            continue

        rows.append(
            {
                "metric_date": timestamp[:10],
                "warehouse_location": warehouse,
                "client_brand": brand,
                "event_type": event_type,
                "quantity": int(quantity),
            }
        )

    if not rows:
        return []

    frame = pd.DataFrame(rows)
    out_rows = []  # type: List[Dict[str, Any]]
    for key, group in frame.groupby(
        ["metric_date", "warehouse_location", "client_brand"], sort=True
    ):
        metric_date, warehouse_location, client_brand = key
        outbound = group[group["event_type"] == "outbound_order_created"]
        inbound = group[group["event_type"] == "inbound_order_created"]
        products = group[group["event_type"] == "product_created"]
        out_rows.append(
            {
                "metric_date": metric_date,
                "warehouse_location": warehouse_location,
                "client_brand": client_brand,
                "outbound_order_count": int(len(outbound)),
                "outbound_unit_quantity": int(outbound["quantity"].sum())
                if len(outbound)
                else 0,
                "inbound_order_count": int(len(inbound)),
                "inbound_unit_quantity": int(inbound["quantity"].sum())
                if len(inbound)
                else 0,
                "product_created_count": int(len(products)),
            }
        )
    return out_rows


@task(
    name="load_executive_kpi_snapshot",
    retries=3,
    # Database writes can fail on transient locks; 3 tries / 5s is enough for SQLite/Postgres.
    retry_delay_seconds=5,
)
def load_executive_kpi_snapshot(
    kpi_rows,
    db_path,
    started_at,
    flow_run_id,
    status="Completed",
    error_message=None,
):
    # type: (List[Dict[str, Any]], str, str, str, str, Optional[str]) -> Dict[str, Any]
    """
    Idempotent upsert of KPI rows + append pipeline_run_log.
    Re-running the same window replaces KPI rows by natural key — no duplicates.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        _ensure_schema(conn)
        for row in kpi_rows:
            conn.execute(
                """
                INSERT INTO daily_warehouse_kpis (
                    metric_date, warehouse_location, client_brand,
                    outbound_order_count, outbound_unit_quantity,
                    inbound_order_count, inbound_unit_quantity,
                    product_created_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(metric_date, warehouse_location, client_brand) DO UPDATE SET
                    outbound_order_count = excluded.outbound_order_count,
                    outbound_unit_quantity = excluded.outbound_unit_quantity,
                    inbound_order_count = excluded.inbound_order_count,
                    inbound_unit_quantity = excluded.inbound_unit_quantity,
                    product_created_count = excluded.product_created_count
                """,
                (
                    row["metric_date"],
                    row["warehouse_location"],
                    row["client_brand"],
                    row["outbound_order_count"],
                    row["outbound_unit_quantity"],
                    row["inbound_order_count"],
                    row["inbound_unit_quantity"],
                    row["product_created_count"],
                ),
            )

        finished_at = _utcnow().isoformat()
        run_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO pipeline_run_log (
                id, flow_run_id, started_at, finished_at,
                records_processed, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                flow_run_id,
                started_at,
                finished_at,
                len(kpi_rows),
                status,
                error_message,
            ),
        )
        conn.commit()
        return {
            "run_id": run_id,
            "records_processed": len(kpi_rows),
            "status": status,
            "finished_at": finished_at,
        }
    finally:
        conn.close()


@task(name="notify_pipeline_status")
def notify_pipeline_status(load_result, fail=False):
    # type: (Dict[str, Any], bool) -> str
    """Optional secondary step (e.g. Slack). Can be forced to fail for resilience demos."""
    if fail:
        raise RuntimeError("Notification channel unavailable")
    return "TrackFlow warehouse ETL {}: {} KPI rows".format(
        load_result.get("status"),
        load_result.get("records_processed"),
    )


# ---------------------------------------------------------------------------
# Subflows
# ---------------------------------------------------------------------------


@flow(name="extract_warehouse_telemetry_subflow")
def extract_warehouse_telemetry_subflow(events_path):
    # type: (str) -> List[Dict[str, Any]]
    return extract_outbound_order_events(events_path)


@flow(name="transform_warehouse_kpi_subflow")
def transform_warehouse_kpi_subflow(events):
    # type: (List[Dict[str, Any]]) -> List[Dict[str, Any]]
    return transform_warehouse_shipment_kpis(events)


@flow(name="load_executive_kpi_subflow")
def load_executive_kpi_subflow(
    kpi_rows,
    db_path,
    started_at,
    flow_run_id,
    status="Completed",
    error_message=None,
):
    # type: (List[Dict[str, Any]], str, str, str, str, Optional[str]) -> Dict[str, Any]
    return load_executive_kpi_snapshot(
        kpi_rows,
        db_path=db_path,
        started_at=started_at,
        flow_run_id=flow_run_id,
        status=status,
        error_message=error_message,
    )


@flow(name="notify_pipeline_status_subflow")
def notify_pipeline_status_subflow(load_result, fail=False):
    # type: (Dict[str, Any], bool) -> str
    return notify_pipeline_status(load_result, fail=fail)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


@flow(name="trackflow_warehouse_telemetry_etl")
def trackflow_warehouse_telemetry_etl(
    events_path=None,
    db_path=None,
    force_notify_failure=False,
):
    # type: (Optional[str], Optional[str], bool) -> Dict[str, Any]
    """
    Main TrackFlow warehouse telemetry ETL.

    Invokes extract -> transform -> load subflows in sequence.
    Notify is optional and uses return_state=True so its failure does not fail the run.
    """
    started_at = _utcnow().isoformat()
    flow_run_id = str(uuid.uuid4())
    source = events_path or str(DEFAULT_EVENTS_PATH)
    database = db_path or str(DEFAULT_DB_PATH)

    events = extract_warehouse_telemetry_subflow(source)
    kpi_rows = transform_warehouse_kpi_subflow(events)

    # Explicit failure handling via return_state=True (assignment requirement)
    load_state = load_executive_kpi_subflow(
        kpi_rows,
        db_path=database,
        started_at=started_at,
        flow_run_id=flow_run_id,
        return_state=True,
    )

    if load_state.is_failed():
        try:
            load_executive_kpi_snapshot(
                [],
                db_path=database,
                started_at=started_at,
                flow_run_id=flow_run_id,
                status="Failed",
                error_message=str(load_state.message),
            )
        except Exception:
            pass
        return {
            "status": "Failed",
            "error": str(load_state.message),
            "flow_run_id": flow_run_id,
        }

    load_result = load_state.result()

    notify_state = notify_pipeline_status_subflow(
        load_result,
        fail=force_notify_failure,
        return_state=True,
    )
    notify_status = (
        "Completed"
        if notify_state.is_completed()
        else "Failed: {}".format(notify_state.message)
    )

    return {
        "status": "Completed",
        "flow_run_id": flow_run_id,
        "records_processed": load_result.get("records_processed", 0),
        "load": load_result,
        "notify_status": notify_status,
        "kpi_rows": kpi_rows,
    }


if __name__ == "__main__":
    result = trackflow_warehouse_telemetry_etl()
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "kpi_rows"},
            indent=2,
        )
    )
    print("KPI rows written: {}".format(result.get("records_processed")))
