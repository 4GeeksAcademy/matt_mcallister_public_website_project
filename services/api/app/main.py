"""FastAPI TrackFlow Incident Manager API."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Repo root for packages.shared imports
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.shared.incident_validation import (  # noqa: E402
    empty_summary,
    is_valid_lifecycle_transition,
    validate_incident_fields,
)
from app.db import connect, ensure_db, row_to_dict  # noqa: E402

app = FastAPI(title="TrackFlow Incident Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IncidentCreate(BaseModel):
    title: str = ""
    description: str = ""
    category: str = ""
    status: str = "open"
    origin: str = ""
    branch: str = ""


class StatusPatch(BaseModel):
    status: str = Field(..., min_length=1)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _field_error(field: str, message: str, *, http_status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"message": "Validation failed", "error": {"field": field, "message": message}},
    )


@app.on_event("startup")
def _startup() -> None:
    ensure_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    field = "body"
    message = "Request validation failed."
    if errors:
        loc = errors[0].get("loc") or ()
        if len(loc) >= 2:
            field = str(loc[-1])
        message = str(errors[0].get("msg") or message)
    return _field_error(field, message)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"message": "Something went wrong. Please try again later."},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/incidents")
def create_incident(body: IncidentCreate) -> JSONResponse:
    errors = validate_incident_fields(
        title=body.title,
        description=body.description,
        category=body.category,
        status=body.status,
        origin=body.origin,
        branch=body.branch,
    )
    if errors:
        return _field_error(errors[0]["field"], errors[0]["message"])

    incident_id = f"inc_{uuid.uuid4().hex[:12]}"
    timestamp = _now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                id, title, description, category, status, origin, branch,
                created_at, updated_at, seed_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                incident_id,
                body.title.strip(),
                body.description.strip(),
                body.category.strip(),
                body.status.strip(),
                body.origin.strip(),
                body.branch.strip(),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()

    return JSONResponse(status_code=201, content={"data": row_to_dict(row)})


@app.get("/api/incidents")
def list_incidents(
    status: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
) -> JSONResponse:
    from packages.shared.incident_validation import (
        branches,
        categories,
        origins,
        statuses,
    )

    for value, allowed, field in (
        (status, statuses(), "status"),
        (origin, origins(), "origin"),
        (branch, branches(), "branch"),
        (category, categories(), "category"),
    ):
        if value is not None and value != "" and value not in allowed:
            return _field_error(field, f"Invalid {field} filter value.")

    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if origin:
        clauses.append("origin = ?")
        params.append(origin)
    if branch:
        clauses.append("branch = ?")
        params.append(branch)
    if category:
        clauses.append("category = ?")
        params.append(category)

    sql = "SELECT * FROM incidents"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    return JSONResponse(content={"data": [row_to_dict(row) for row in rows]})


@app.get("/api/incidents/summary")
def summary() -> JSONResponse:
    result = empty_summary()
    with connect() as conn:
        rows = conn.execute("SELECT status, category, origin, branch FROM incidents").fetchall()
    for row in rows:
        result["by_status"][row["status"]] = result["by_status"].get(row["status"], 0) + 1
        result["by_category"][row["category"]] = result["by_category"].get(row["category"], 0) + 1
        result["by_origin"][row["origin"]] = result["by_origin"].get(row["origin"], 0) + 1
        result["by_branch"][row["branch"]] = result["by_branch"].get(row["branch"], 0) + 1
    return JSONResponse(content={"data": result})


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> JSONResponse:
    with connect() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"message": "Incident not found."})
    return JSONResponse(content={"data": row_to_dict(row)})


@app.patch("/api/incidents/{incident_id}/status")
def patch_status(incident_id: str, body: StatusPatch) -> JSONResponse:
    next_status = body.status.strip()
    from packages.shared.incident_validation import statuses

    if next_status not in statuses():
        return _field_error("status", "Status value is not allowed.")

    with connect() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"message": "Incident not found."})

        current = row["status"]
        if current == next_status:
            return JSONResponse(content={"data": row_to_dict(row)})

        if not is_valid_lifecycle_transition(current, next_status):
            return _field_error(
                "status",
                f"Cannot move incident from {current} to {next_status}.",
            )

        updated_at = _now()
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (next_status, updated_at, incident_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()

    return JSONResponse(content={"data": row_to_dict(updated)})
