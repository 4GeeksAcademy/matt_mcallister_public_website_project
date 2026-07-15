"""Pandas analysis pipeline for operational telemetry metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def _to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=["timestamp", "event_type", "tags", "day", "warehouse", "client_id"]
        )
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["day"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    tags = df["tags"].apply(lambda t: t if isinstance(t, dict) else {})
    df["warehouse"] = tags.apply(lambda t: t.get("warehouse"))
    df["client_id"] = tags.apply(lambda t: t.get("client_id"))
    return df


def events_per_day(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Daily event volume overall and by event_type within the period."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    grouped = (
        df.groupby(["day", "event_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["day", "event_type"])
    )
    return grouped.to_dict(orient="records")


def order_volume_by_warehouse(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Inbound/outbound order volume per day per warehouse."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    orders = df[
        df["event_type"].isin(["inbound_order_created", "outbound_order_created"])
    ]
    if orders.empty:
        return []
    grouped = (
        orders.groupby(["day", "warehouse", "event_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["day", "warehouse", "event_type"])
    )
    return grouped.to_dict(orient="records")


def stock_threshold_rate_by_client(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Stock threshold breach rate per client (breaches / outbound events)."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    outbound = df[df["event_type"] == "outbound_order_created"]
    breaches = df[df["event_type"] == "stock_threshold_triggered"]
    out_counts = outbound.groupby("client_id").size().rename("outbound_count")
    breach_counts = breaches.groupby("client_id").size().rename("breach_count")
    merged = pd.concat([out_counts, breach_counts], axis=1).fillna(0)
    if merged.empty:
        return []
    merged["breach_rate"] = merged["breach_count"] / merged["outbound_count"].replace(
        0, pd.NA
    )
    merged = merged.reset_index().fillna({"breach_rate": 0.0})
    return merged.to_dict(orient="records")


def discrepancy_rate_by_warehouse(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Discrepancy events per warehouse vs total inventory events."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    inventory_types = [
        "inbound_order_created",
        "outbound_order_created",
        "stock_threshold_triggered",
        "direct_stock_edit_rejected",
        "inventory_discrepancy_detected",
    ]
    inv = df[df["event_type"].isin(inventory_types)]
    if inv.empty:
        return []
    total = inv.groupby("warehouse").size().rename("inventory_events")
    disc = (
        inv[inv["event_type"] == "inventory_discrepancy_detected"]
        .groupby("warehouse")
        .size()
        .rename("discrepancy_count")
    )
    merged = pd.concat([total, disc], axis=1).fillna(0)
    merged["discrepancy_rate"] = merged["discrepancy_count"] / merged[
        "inventory_events"
    ].replace(0, pd.NA)
    merged = merged.reset_index().fillna({"discrepancy_rate": 0.0})
    return merged.to_dict(orient="records")


def auth_failure_rate(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Daily login failure rate: failed / (failed + succeeded)."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    auth = df[
        df["event_type"].isin(["user_login_failed", "user_login_succeeded"])
    ].copy()
    if auth.empty:
        return []
    pivot = (
        auth.groupby(["day", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "user_login_failed" not in pivot.columns:
        pivot["user_login_failed"] = 0
    if "user_login_succeeded" not in pivot.columns:
        pivot["user_login_succeeded"] = 0
    pivot["total_attempts"] = (
        pivot["user_login_failed"] + pivot["user_login_succeeded"]
    )
    pivot["failure_rate"] = pivot["user_login_failed"] / pivot["total_attempts"].replace(
        0, pd.NA
    )
    pivot = pivot.fillna({"failure_rate": 0.0})
    return pivot[
        ["day", "user_login_failed", "user_login_succeeded", "total_attempts", "failure_rate"]
    ].to_dict(orient="records")


def error_rate_by_type(
    rows: list[dict[str, Any]],
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Share of frontend/technical error events among all events per day."""
    _ = (start_date, end_date)
    df = _to_frame(rows)
    if df.empty:
        return []
    error_types = [
        "frontend_error_uncaught",
        "user_login_failed",
        "inbound_order_validation_failed",
    ]
    daily_total = df.groupby("day").size().rename("total")
    daily_err = (
        df[df["event_type"].isin(error_types)]
        .groupby(["day", "event_type"])
        .size()
        .reset_index(name="count")
    )
    if daily_err.empty:
        return []
    merged = daily_err.merge(daily_total, on="day", how="left")
    merged["rate"] = merged["count"] / merged["total"]
    return merged.to_dict(orient="records")
