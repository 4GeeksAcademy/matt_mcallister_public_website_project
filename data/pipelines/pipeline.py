"""
TrackFlow Weekly Warehouse & Client Performance ETL (Prefect).

Weekly pipeline: extract mandatory warehouse telemetry → aggregate per
(warehouse, client_id, week_start) → idempotent upsert into
reporting.weekly_warehouse_client_performance + reporting.pipeline_runs.

Schedule: Mondays ~07:00 (UTC Monday morning). See PIPELINE_DESIGN.md.

Run from monorepo root:
    python data/pipelines/pipeline.py

Optional week override:
    WEEK_START=2026-07-06 python data/pipelines/pipeline.py
"""

import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
# Keep Prefect's ephemeral SQLite under the repo so local CLI runs work offline.
# Must be set before importing prefect.
_PREFECT_HOME = REPO_ROOT / "data" / "pipelines" / ".prefect"
_PREFECT_HOME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PREFECT_HOME", str(_PREFECT_HOME))

from prefect import flow, task  # noqa: E402
from prefect.tasks import task_input_hash  # noqa: E402

DEFAULT_EVENTS_PATH = REPO_ROOT / "data" / "raw" / "telemetry_events.jsonl"

PIPELINE_EVENT_TYPES = frozenset(
    {
        "inbound_order_created",
        "outbound_order_created",
        "stock_threshold_triggered",
        "inventory_discrepancy_detected",
    }
)
VALID_WAREHOUSES = frozenset({"los_angeles", "zaragoza"})


def _utcnow():
    # type: () -> datetime
    return datetime.now(timezone.utc)


def iso_week_start(ts):
    # type: (datetime) -> date
    """Return Monday (UTC) of the ISO week containing ts."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    d = ts.date()
    return d - timedelta(days=d.weekday())


def resolve_week_start(week_start=None):
    # type: (Optional[str]) -> date
    if week_start is None or week_start == "":
        env = os.getenv("WEEK_START")
        if env:
            return date.fromisoformat(env)
        today = _utcnow().date()
        this_monday = today - timedelta(days=today.weekday())
        return this_monday - timedelta(days=7)
    if isinstance(week_start, date) and not isinstance(week_start, datetime):
        return week_start
    return date.fromisoformat(str(week_start))


def _parse_timestamp(value):
    # type: (Any) -> Optional[datetime]
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        ts = datetime.fromisoformat(text)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _props(event):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    if isinstance(event.get("properties"), dict):
        return event["properties"]
    if isinstance(event.get("tags"), dict):
        return event["tags"]
    return {}


def normalize_event(raw):
    # type: (Dict[str, Any]) -> Optional[Dict[str, Any]]
    """Validate and normalize a telemetry row for KPI aggregation."""
    if not isinstance(raw, dict):
        return None
    event_type = raw.get("event_type")
    if event_type not in PIPELINE_EVENT_TYPES:
        return None
    ts = _parse_timestamp(raw.get("timestamp"))
    if ts is None:
        return None
    props = _props(raw)
    warehouse = props.get("warehouse")
    client_id = props.get("client_id")
    if warehouse not in VALID_WAREHOUSES or not client_id:
        return None
    quantity = props.get("quantity", 0)
    try:
        quantity_num = float(quantity) if quantity is not None else 0.0
    except (TypeError, ValueError):
        quantity_num = 0.0
    week = iso_week_start(ts)
    return {
        "event_type": event_type,
        "timestamp": ts.isoformat(),
        "week_start": week.isoformat(),
        "warehouse": warehouse,
        "client_id": str(client_id),
        "quantity": quantity_num,
    }


from reporting_store import (  # noqa: E402
    DEFAULT_DB_PATH,
    _get_supabase,
    get_latest_pipeline_run,
    insert_pipeline_run,
    query_weekly_performance,
    upsert_weekly_rows,
)

# Re-export store helpers for services/reporting and callers that import from pipeline.
__all__ = [
    "DEFAULT_DB_PATH",
    "get_latest_pipeline_run",
    "query_weekly_performance",
    "weekly_warehouse_client_performance_etl",
]


def _grain_key(warehouse, client_id):
    # type: (Any, Any) -> Optional[str]
    if warehouse not in VALID_WAREHOUSES or not client_id:
        return None
    return "{}::{}".format(warehouse, client_id)


def _split_grain_key(key):
    # type: (str) -> Tuple[str, str]
    warehouse, client_id = key.split("::", 1)
    return warehouse, client_id


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@task(
    name="extract_weekly_warehouse_events",
    # Transient Supabase / network blips: 3 retries with short backoff.
    retries=3,
    retry_delay_seconds=5,
)
def extract_weekly_warehouse_events(week_start, events_path=None):
    # type: (str, Optional[str]) -> List[Dict[str, Any]]
    """Extract mandatory event types for the target ISO week (read-only)."""
    target = resolve_week_start(week_start)
    week_end = target + timedelta(days=7)
    start_iso = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    end_iso = datetime.combine(week_end, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    target_iso = target.isoformat()

    client = _get_supabase()
    raw_events = []  # type: List[Dict[str, Any]]
    if client is not None:
        try:
            result = (
                client.table("telemetry_events")
                .select("*")
                .gte("timestamp", start_iso)
                .lt("timestamp", end_iso)
                .in_("event_type", list(PIPELINE_EVENT_TYPES))
                .execute()
            )
            raw_events = list(result.data or [])
        except Exception:
            raw_events = []

    if not raw_events:
        path = Path(events_path) if events_path else DEFAULT_EVENTS_PATH
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    normalized = []  # type: List[Dict[str, Any]]
    for raw in raw_events:
        event = normalize_event(raw)
        if event is None:
            continue
        if event["week_start"] != target_iso:
            continue
        normalized.append(event)
    return normalized


@task(name="compute_inbound_units_count")
def compute_inbound_units_count(events):
    # type: (List[Dict[str, Any]]) -> Dict[str, int]
    """Inbound Volume: sum of quantities from inbound_order_created."""
    totals = {}  # type: Dict[str, int]
    if not isinstance(events, list):
        return totals
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "inbound_order_created":
            continue
        key = _grain_key(event.get("warehouse"), event.get("client_id"))
        if key is None:
            continue
        qty = event.get("quantity", 0)
        try:
            totals[key] = totals.get(key, 0) + int(float(qty))
        except (TypeError, ValueError):
            continue
    return totals


@task(name="compute_outbound_orders_count")
def compute_outbound_orders_count(events):
    # type: (List[Dict[str, Any]]) -> Dict[str, int]
    """Outbound Throughput: count of outbound_order_created events."""
    totals = {}  # type: Dict[str, int]
    if not isinstance(events, list):
        return totals
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "outbound_order_created":
            continue
        key = _grain_key(event.get("warehouse"), event.get("client_id"))
        if key is None:
            continue
        totals[key] = totals.get(key, 0) + 1
    return totals


@task(name="compute_stockout_events_count")
def compute_stockout_events_count(events):
    # type: (List[Dict[str, Any]]) -> Dict[str, int]
    """Stockout Frequency: count of stock_threshold_triggered events."""
    totals = {}  # type: Dict[str, int]
    if not isinstance(events, list):
        return totals
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "stock_threshold_triggered":
            continue
        key = _grain_key(event.get("warehouse"), event.get("client_id"))
        if key is None:
            continue
        totals[key] = totals.get(key, 0) + 1
    return totals


@task(name="compute_discrepancy_rate")
def compute_discrepancy_rate(events, outbound_counts):
    # type: (List[Dict[str, Any]], Dict[str, int]) -> Dict[str, Dict[str, float]]
    """Discrepancy Rate: discrepancy_events_count / outbound_orders_count (0 if none)."""
    disc_counts = {}  # type: Dict[str, int]
    if not isinstance(events, list):
        return {}
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "inventory_discrepancy_detected":
            continue
        key = _grain_key(event.get("warehouse"), event.get("client_id"))
        if key is None:
            continue
        disc_counts[key] = disc_counts.get(key, 0) + 1

    keys = set(disc_counts) | set(outbound_counts or {})
    result = {}  # type: Dict[str, Dict[str, float]]
    for key in keys:
        disc = disc_counts.get(key, 0)
        outbound = int((outbound_counts or {}).get(key, 0))
        rate = (disc / outbound) if outbound > 0 else 0.0
        result[key] = {
            "discrepancy_events_count": float(disc),
            "discrepancy_rate": rate,
        }
    return result


@task(
    name="assemble_weekly_warehouse_client_rows",
    # Cache key derived from task inputs via task_input_hash (week_start + KPI maps).
    # Expiration 1 hour: Monday debug re-runs reuse the join without recompute.
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def assemble_weekly_warehouse_client_rows(
    week_start, inbound, outbound, stockouts, discrepancies
):
    # type: (str, Dict[str, int], Dict[str, int], Dict[str, int], Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]
    """Join KPI maps into destination-shaped rows (expensive join cached 1h)."""
    week_iso = resolve_week_start(week_start).isoformat()
    keys = set(inbound or {}) | set(outbound or {}) | set(stockouts or {}) | set(
        discrepancies or {}
    )
    rows = []  # type: List[Dict[str, Any]]
    for key in sorted(keys):
        warehouse, client_id = _split_grain_key(key)
        if warehouse not in VALID_WAREHOUSES or not client_id:
            continue
        disc = (discrepancies or {}).get(key, {})
        rows.append(
            {
                "warehouse": warehouse,
                "client_id": client_id,
                "week_start": week_iso,
                "inbound_units_count": int((inbound or {}).get(key, 0)),
                "outbound_orders_count": int((outbound or {}).get(key, 0)),
                "stockout_events_count": int((stockouts or {}).get(key, 0)),
                "discrepancy_events_count": int(disc.get("discrepancy_events_count", 0)),
                "discrepancy_rate": float(disc.get("discrepancy_rate", 0.0)),
            }
        )
    return rows


@task(
    name="load_weekly_warehouse_client_performance",
    # DB upsert can flake on connectivity; 3 retries with 10s delay.
    retries=3,
    retry_delay_seconds=10,
)
def load_weekly_warehouse_client_performance(rows, db_path=None):
    # type: (List[Dict[str, Any]], Optional[str]) -> int
    """Idempotent upsert keyed by unique (warehouse, client_id, week_start)."""
    return upsert_weekly_rows(rows, db_path=db_path)


@task(
    name="record_pipeline_run",
    retries=3,
    retry_delay_seconds=5,
)
def record_pipeline_run(
    run_id,
    week_start,
    started_at,
    finished_at,
    records_processed,
    status,
    error_message=None,
    flow_run_id=None,
    db_path=None,
):
    # type: (str, str, str, str, int, str, Optional[str], Optional[str], Optional[str]) -> Dict[str, Any]
    """Append execution metadata for production auditing."""
    week_iso = resolve_week_start(week_start).isoformat()
    row = {
        "id": run_id,
        "flow_run_id": flow_run_id,
        "week_start": week_iso,
        "started_at": started_at,
        "finished_at": finished_at,
        "records_processed": records_processed,
        "status": status,
        "error_message": error_message,
    }
    return insert_pipeline_run(row, db_path=db_path)


@task(name="notify_weekly_pipeline_status")
def notify_weekly_pipeline_status(status, records_processed, force_failure=False):
    # type: (str, int, bool) -> str
    """Optional notification step (console). Failures are isolated by the flow."""
    if force_failure:
        raise RuntimeError("Forced notify failure for resilience demo")
    message = "[TrackFlow] weekly warehouse pipeline {}; records={}".format(
        status, records_processed
    )
    print(message)
    return message


# ---------------------------------------------------------------------------
# Subflows
# ---------------------------------------------------------------------------


@flow(name="extract_weekly_warehouse_events_subflow")
def extract_weekly_warehouse_events_subflow(week_start, events_path=None):
    # type: (str, Optional[str]) -> List[Dict[str, Any]]
    return extract_weekly_warehouse_events(week_start, events_path)


@flow(name="transform_weekly_warehouse_client_kpis_subflow")
def transform_weekly_warehouse_client_kpis_subflow(week_start, events):
    # type: (str, List[Dict[str, Any]]) -> List[Dict[str, Any]]
    inbound = compute_inbound_units_count(events)
    outbound = compute_outbound_orders_count(events)
    stockouts = compute_stockout_events_count(events)
    discrepancies = compute_discrepancy_rate(events, outbound)
    return assemble_weekly_warehouse_client_rows(
        week_start, inbound, outbound, stockouts, discrepancies
    )


@flow(name="load_weekly_warehouse_client_performance_subflow")
def load_weekly_warehouse_client_performance_subflow(rows, db_path=None):
    # type: (List[Dict[str, Any]], Optional[str]) -> int
    return load_weekly_warehouse_client_performance(rows, db_path)


@flow(name="notify_weekly_pipeline_status_subflow")
def notify_weekly_pipeline_status_subflow(status, records_processed, force_failure=False):
    # type: (str, int, bool) -> str
    return notify_weekly_pipeline_status(status, records_processed, force_failure)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


@flow(name="weekly_warehouse_client_performance_etl")
def weekly_warehouse_client_performance_etl(
    week_start=None,
    events_path=None,
    db_path=None,
    force_notify_failure=False,
):
    # type: (Optional[str], Optional[str], Optional[str], bool) -> Dict[str, Any]
    """Main ETL: extract → transform → load → optional notify."""
    started = _utcnow()
    run_id = str(uuid.uuid4())
    target_week = resolve_week_start(week_start)
    target_iso = target_week.isoformat()
    error_message = None  # type: Optional[str]
    status = "Completed"
    records = 0
    notify_status = None  # type: Optional[str]

    try:
        events = extract_weekly_warehouse_events_subflow(target_iso, events_path)
        rows = transform_weekly_warehouse_client_kpis_subflow(target_iso, events)
        records = load_weekly_warehouse_client_performance_subflow(rows, db_path)
    except Exception as exc:
        status = "Failed"
        error_message = str(exc)
        finished = _utcnow()
        record_pipeline_run(
            run_id=run_id,
            week_start=target_iso,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            records_processed=records,
            status=status,
            error_message=error_message,
            db_path=db_path,
        )
        raise

    finished = _utcnow()
    record_pipeline_run(
        run_id=run_id,
        week_start=target_iso,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        records_processed=records,
        status=status,
        error_message=None,
        db_path=db_path,
    )

    # Optional step: isolate failure so notify errors do not fail the ETL.
    notify_state = notify_weekly_pipeline_status_subflow(
        status, records, force_notify_failure, return_state=True
    )
    notify_status = str(notify_state.type) if notify_state is not None else None

    return {
        "status": status,
        "week_start": target_iso,
        "records_processed": records,
        "run_id": run_id,
        "notify_status": notify_status,
        "error": error_message,
    }


if __name__ == "__main__":
    # Intended schedule: Mondays ~07:00 UTC. Manual / CI: this CLI entrypoint.
    force_notify = os.getenv("FORCE_NOTIFY_FAILURE", "").lower() in {"1", "true", "yes"}
    result = weekly_warehouse_client_performance_etl(force_notify_failure=force_notify)
    print(json.dumps(result, indent=2))
