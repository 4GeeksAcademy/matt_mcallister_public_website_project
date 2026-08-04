"""Focused tests for nightly telemetry KPI aggregation and orchestration."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from data.pipelines.telemetry_kpi_daily import run as pipeline


def test_aggregate_daily_kpis_returns_useful_daily_metrics() -> None:
    cursor = MagicMock()
    cursor.fetchone.return_value = (
        7,
        3,
        {"page_viewed": 5, "incident_created": 2},
    )
    day = date(2026, 8, 3)

    result = pipeline.aggregate_daily_kpis(cursor, day)

    assert result == {
        "target_date": day,
        "event_count": 7,
        "unique_user_count": 3,
        "event_type_counts": {"page_viewed": 5, "incident_created": 2},
    }
    assert cursor.execute.call_args.args[1] == (day, day)


def test_persist_daily_kpis_uses_target_date_upsert() -> None:
    cursor = MagicMock()

    pipeline.persist_daily_kpis(
        cursor,
        {
            "target_date": date(2026, 8, 3),
            "event_count": 7,
            "unique_user_count": 3,
            "event_type_counts": {"page_viewed": 7},
        },
    )

    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert any("reporting.telemetry_kpi_daily" in sql for sql in statements)
    assert any("ON CONFLICT (target_date) DO UPDATE" in sql for sql in statements)


def test_run_tracks_completion_and_is_safe_to_orchestrate_twice(monkeypatch) -> None:
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    get_connection = MagicMock(return_value=connection)
    start = MagicMock(side_effect=[{"id": 41}, {"id": 42}])
    finish = MagicMock()
    aggregate = MagicMock(
        return_value={
            "target_date": date(2026, 8, 3),
            "event_count": 7,
            "unique_user_count": 3,
            "event_type_counts": {"page_viewed": 7},
        }
    )
    persist = MagicMock()
    monkeypatch.setattr(pipeline, "get_connection", get_connection)
    monkeypatch.setattr(pipeline, "start_pipeline_run", start)
    monkeypatch.setattr(pipeline, "finish_pipeline_run", finish)
    monkeypatch.setattr(pipeline, "aggregate_daily_kpis", aggregate)
    monkeypatch.setattr(pipeline, "persist_daily_kpis", persist)
    day = date(2026, 8, 3)

    assert pipeline.run(target_date=day) == 0
    assert pipeline.run(target_date=day) == 0

    assert start.call_count == 2
    assert aggregate.call_count == 2
    assert persist.call_count == 2
    assert connection.commit.call_count == 2
    assert finish.call_args_list[0].args == (41,)
    assert finish.call_args_list[0].kwargs == {"status": "completed"}
    assert finish.call_args_list[1].args == (42,)
    assert finish.call_args_list[1].kwargs == {"status": "completed"}
