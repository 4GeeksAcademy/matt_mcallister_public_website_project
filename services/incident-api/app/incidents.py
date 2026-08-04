from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from app.db import connect, row_to_dict
from packages.shared.incident_validation import validate_incident_fields


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOMAIN = json.loads(
    (_REPO_ROOT / "packages" / "shared" / "incident-domain.json").read_text(
        encoding="utf-8"
    )
)
_LIFECYCLE: dict[str, list[str]] = _DOMAIN["lifecycle"]

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=5000)
    category: str
    status: str
    origin: str
    branch: str


class StatusUpdate(BaseModel):
    status: str


def _field_error(
    field: str, message: str, status_code: int = 422
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"field": field, "message": message}},
    )


def _validate(payload: IncidentCreate) -> JSONResponse | None:
    errors = validate_incident_fields(**payload.model_dump())
    if errors:
        error = errors[0]
        return _field_error(error["field"], error["message"])
    return None


def _response(data=None, message: str | None = None) -> dict:
    payload: dict = {}
    if data is not None:
        payload["data"] = data
    if message is not None:
        payload["message"] = message
    return payload


@router.get("")
def list_incidents(
    incident_status: str | None = Query(default=None, alias="status"),
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> dict:
    clauses: list[str] = []
    values: list[str] = []
    for column, value in (
        ("status", incident_status),
        ("origin", origin),
        ("branch", branch),
        ("category", category),
    ):
        if value:
            clauses.append(f"{column} = ?")
            values.append(value)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM incidents{where} ORDER BY created_at DESC", values
        ).fetchall()
    return _response([row_to_dict(row) for row in rows])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate):
    validation_error = _validate(payload)
    if validation_error is not None:
        return validation_error
    now = datetime.now(timezone.utc).isoformat()
    incident = {
        "id": f"inc_{uuid4().hex}",
        **payload.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                id, title, description, category, status, origin, branch,
                created_at, updated_at, seed_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                incident["id"],
                incident["title"],
                incident["description"],
                incident["category"],
                incident["status"],
                incident["origin"],
                incident["branch"],
                incident["created_at"],
                incident["updated_at"],
            ),
        )
        conn.commit()
    return _response(incident, "Incident registered successfully.")


@router.get("/summary")
def incident_summary() -> dict:
    def counts(column: str) -> dict[str, int]:
        with connect() as conn:
            rows = conn.execute(
                f"SELECT {column}, COUNT(*) AS count FROM incidents GROUP BY {column}"
            ).fetchall()
        return {row[column]: row["count"] for row in rows}

    return _response(
        {
            "by_status": counts("status"),
            "by_category": counts("category"),
            "by_origin": counts("origin"),
            "by_branch": counts("branch"),
        }
    )


@router.get("/{incident_id}")
def get_incident(incident_id: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _response(row_to_dict(row))


@router.patch("/{incident_id}/status")
def update_incident_status(incident_id: str, payload: StatusUpdate):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Incident not found")

        current_status = row["status"]
        allowed = _LIFECYCLE.get(current_status, [])
        if payload.status not in allowed:
            return _field_error(
                "status",
                f"Cannot transition incident from {current_status} to {payload.status}.",
                status_code=409,
            )

        updated_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (payload.status, updated_at, incident_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
    return _response(row_to_dict(updated))


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_incident(incident_id: str) -> None:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Incident not found")
        conn.commit()
