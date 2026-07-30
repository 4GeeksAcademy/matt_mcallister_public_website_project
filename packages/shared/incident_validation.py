"""Shared TrackFlow incident validation and CSV mapping helpers.

Loads allowed values and maps from packages/shared/incident-domain.json so the
seed script and FastAPI service stay aligned with CONTEXT-incidents.md.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DOMAIN_PATH = Path(__file__).resolve().parent / "incident-domain.json"


@lru_cache(maxsize=1)
def load_domain() -> dict[str, Any]:
    return json.loads(_DOMAIN_PATH.read_text(encoding="utf-8"))


def statuses() -> set[str]:
    return set(load_domain()["statuses"])


def origins() -> set[str]:
    return set(load_domain()["origins"])


def categories() -> set[str]:
    return set(load_domain()["categories"])


def branches() -> set[str]:
    return set(load_domain()["branches"])


def lifecycle() -> dict[str, list[str]]:
    return dict(load_domain()["lifecycle"])


def csv_status_map() -> dict[str, str]:
    return {k.upper(): v for k, v in load_domain()["csv_status_map"].items()}


def csv_category_map() -> dict[str, str]:
    return {k.upper(): v for k, v in load_domain()["csv_category_map"].items()}


def csv_country_map() -> dict[str, str]:
    return {k.upper(): v for k, v in load_domain()["csv_country_map"].items()}


def empty_summary() -> dict[str, dict[str, int]]:
    return {
        "by_status": {key: 0 for key in load_domain()["statuses"]},
        "by_category": {key: 0 for key in load_domain()["categories"]},
        "by_origin": {key: 0 for key in load_domain()["origins"]},
        "by_branch": {key: 0 for key in load_domain()["branches"]},
    }


def map_status(raw: str) -> str | None:
    value = (raw or "").strip()
    if value in statuses():
        return value
    return csv_status_map().get(value.upper())


def map_category(raw: str) -> str | None:
    value = (raw or "").strip()
    if value in categories():
        return value
    return csv_category_map().get(value.upper())


def map_branch_from_country(raw: str) -> str | None:
    value = (raw or "").strip()
    if value in branches():
        return value
    return csv_country_map().get(value.upper())


def is_valid_lifecycle_transition(current: str, nxt: str) -> bool:
    return nxt in lifecycle().get(current, [])


def validate_incident_fields(
    *,
    title: str,
    description: str,
    category: str,
    status: str,
    origin: str,
    branch: str,
) -> list[dict[str, str]]:
    """Return a list of {field, message} errors (empty if valid)."""
    errors: list[dict[str, str]] = []

    if not (title or "").strip():
        errors.append({"field": "title", "message": "Title is required."})
    if not (description or "").strip():
        errors.append({"field": "description", "message": "Description is required."})

    if not (category or "").strip():
        errors.append({"field": "category", "message": "Category is required."})
    elif category not in categories():
        errors.append({"field": "category", "message": "Category value is not allowed."})

    if not (status or "").strip():
        errors.append({"field": "status", "message": "Status is required."})
    elif status not in statuses():
        errors.append({"field": "status", "message": "Status value is not allowed."})

    if not (origin or "").strip():
        errors.append({"field": "origin", "message": "Origin is required."})
    elif origin not in origins():
        errors.append({"field": "origin", "message": "Origin value is not allowed."})

    if not (branch or "").strip():
        errors.append({"field": "branch", "message": "Branch is required."})
    elif branch not in branches():
        errors.append({"field": "branch", "message": "Branch value is not allowed."})

    return errors
