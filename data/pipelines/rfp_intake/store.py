"""Persistence layer for RFP tickets (in-memory + PostgreSQL)."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Optional

from data.pipelines.rfp_intake.models import (
    DepartmentProgress,
    DepartmentSummary,
    EvaluationResult,
    NodeLogEntry,
    RfpTicket,
    SectionDraft,
)

_MEMORY: dict[str, dict[str, Any]] = {"tickets": {}, "node_logs": []}


def reset_rfp_store() -> None:
    _MEMORY["tickets"].clear()
    _MEMORY["node_logs"].clear()


class RfpStore:
    """Abstract store operations used by the RFP pipeline."""

    def create_ticket(self, *, filename: str, pdf_path: str) -> RfpTicket:
        raise NotImplementedError

    def get_ticket(self, ticket_id: str) -> Optional[RfpTicket]:
        raise NotImplementedError

    def save_ticket(self, ticket: RfpTicket) -> RfpTicket:
        raise NotImplementedError

    def append_node_log(self, entry: NodeLogEntry) -> None:
        raise NotImplementedError

    def list_node_logs(self, ticket_id: str) -> list[NodeLogEntry]:
        raise NotImplementedError


class InMemoryRfpStore(RfpStore):
    def create_ticket(self, *, filename: str, pdf_path: str) -> RfpTicket:
        ticket = RfpTicket(filename=filename, pdf_path=pdf_path)
        _MEMORY["tickets"][ticket.id] = ticket.model_dump()
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[RfpTicket]:
        raw = _MEMORY["tickets"].get(ticket_id)
        return RfpTicket.model_validate(raw) if raw else None

    def save_ticket(self, ticket: RfpTicket) -> RfpTicket:
        _MEMORY["tickets"][ticket.id] = ticket.model_dump()
        return ticket

    def append_node_log(self, entry: NodeLogEntry) -> None:
        _MEMORY["node_logs"].append(entry.model_dump())

    def list_node_logs(self, ticket_id: str) -> list[NodeLogEntry]:
        return [
            NodeLogEntry.model_validate(item)
            for item in _MEMORY["node_logs"]
            if item.get("ticket_id") == ticket_id
        ]


class PostgresRfpStore(RfpStore):
    def __init__(self, conninfo: str) -> None:
        import psycopg

        self._conninfo = conninfo
        self._psycopg = psycopg

    def _connect(self):
        return self._psycopg.connect(self._conninfo)

    def create_ticket(self, *, filename: str, pdf_path: str) -> RfpTicket:
        ticket = RfpTicket(filename=filename, pdf_path=pdf_path)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rfp_tickets
                    (id, filename, status, pdf_path, metadata, readability_metrics, payload, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                    """,
                    (
                        ticket.id,
                        ticket.filename,
                        ticket.status,
                        ticket.pdf_path,
                        json.dumps(ticket.metadata),
                        json.dumps(ticket.readability_metrics),
                        json.dumps(ticket.model_dump()),
                        ticket.created_at,
                        ticket.updated_at,
                    ),
                )
            conn.commit()
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[RfpTicket]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM rfp_tickets WHERE id = %s",
                    (ticket_id,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return RfpTicket.model_validate(row[0])

    def save_ticket(self, ticket: RfpTicket) -> RfpTicket:
        payload = ticket.model_dump()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE rfp_tickets
                    SET status = %s,
                        metadata = %s::jsonb,
                        readability_metrics = %s::jsonb,
                        error_message = %s,
                        payload = %s::jsonb,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        ticket.status,
                        json.dumps(ticket.metadata),
                        json.dumps(ticket.readability_metrics),
                        ticket.error_message,
                        json.dumps(payload),
                        ticket.id,
                    ),
                )
            conn.commit()
        return ticket

    def append_node_log(self, entry: NodeLogEntry) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rfp_node_logs
                    (ticket_id, department_id, node, agent, input_summary, output_summary, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        entry.ticket_id,
                        entry.department_id,
                        entry.node,
                        entry.agent,
                        entry.input_summary,
                        entry.output_summary,
                        entry.timestamp,
                    ),
                )
            conn.commit()

    def list_node_logs(self, ticket_id: str) -> list[NodeLogEntry]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ticket_id, department_id, node, agent, input_summary, output_summary, timestamp
                    FROM rfp_node_logs WHERE ticket_id = %s ORDER BY timestamp
                    """,
                    (ticket_id,),
                )
                rows = cur.fetchall()
        return [
            NodeLogEntry(
                ticket_id=row[0],
                department_id=row[1],
                node=row[2],
                agent=row[3],
                input_summary=row[4] or "",
                output_summary=row[5] or "",
                timestamp=row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            )
            for row in rows
        ]


def get_rfp_store() -> RfpStore:
    backend = os.environ.get("RFP_STORE_BACKEND", "").lower()
    if backend == "memory":
        return InMemoryRfpStore()
    if backend == "postgres" or os.environ.get("DATABASE_URL"):
        from services.job_runner.db import get_database_url

        return PostgresRfpStore(get_database_url())
    return InMemoryRfpStore()


def ticket_to_progress(ticket: RfpTicket) -> dict[str, Any]:
    return {
        "ticket_id": ticket.id,
        "status": ticket.status,
        "filename": ticket.filename,
        "metadata": ticket.metadata,
        "readability_metrics": ticket.readability_metrics,
        "departments": {
            dept_id: progress.model_dump()
            for dept_id, progress in ticket.department_progress.items()
        },
        "evaluations": {
            dept_id: evaluation.model_dump()
            for dept_id, evaluation in ticket.evaluations.items()
        },
        "has_final_document": ticket.final_document is not None,
        "error_message": ticket.error_message,
    }


def merge_department_summary(ticket: RfpTicket, summary: DepartmentSummary) -> RfpTicket:
    updated = deepcopy(ticket)
    updated.department_summaries = [
        item for item in updated.department_summaries if item.department_id != summary.department_id
    ] + [summary]
    if summary.department_id not in updated.department_progress:
        updated.department_progress[summary.department_id] = DepartmentProgress(
            department_id=summary.department_id
        )
    updated.updated_at = ticket.updated_at
    return updated


def merge_draft(ticket: RfpTicket, draft: SectionDraft) -> RfpTicket:
    updated = deepcopy(ticket)
    updated.drafts[draft.department_id] = draft
    return updated


def merge_evaluation(ticket: RfpTicket, evaluation: EvaluationResult) -> RfpTicket:
    updated = deepcopy(ticket)
    updated.evaluations[evaluation.department_id] = evaluation
    progress = updated.department_progress.get(evaluation.department_id)
    if progress is None:
        progress = DepartmentProgress(department_id=evaluation.department_id)
    progress.latest_evaluation = evaluation
    progress.iteration = updated.drafts.get(evaluation.department_id, SectionDraft(department_id=evaluation.department_id)).iteration
    updated.department_progress[evaluation.department_id] = progress
    return updated
