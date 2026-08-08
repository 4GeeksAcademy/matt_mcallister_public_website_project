from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "DATABASE_URL", "postgresql://trackflow:trackflow@localhost:5432/trackflow"
)

from app.main import app


client = TestClient(app)
fixture_path = (
    Path(__file__).resolve().parents[3] / "data" / "raw" / "incidents-trackflow.csv"
)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_export_route_is_registered_once() -> None:
    export_routes = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/export"
        and "POST" in getattr(route, "methods", set())
    ]

    assert len(export_routes) == 1


def test_analyze_then_export_latest_results() -> None:
    with fixture_path.open("rb") as fixture:
        analyze = client.post(
            "/api/incidents/analyze",
            files={"file": (fixture_path.name, fixture, "text/csv")},
        )

    assert analyze.status_code == 200
    assert analyze.json()["total_records"] == 100

    export = client.get("/api/incidents/results/export")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "total_records" in export.text


def test_legacy_export_analyzes_uploaded_csv() -> None:
    with fixture_path.open("rb") as fixture:
        response = client.post(
            "/export",
            files={"file": (fixture_path.name, fixture, "text/csv")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_incident_crud_filters_summary_and_lifecycle(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("INCIDENTS_DB_PATH", str(tmp_path / "incidents.db"))
    payload = {
        "title": "Delayed carrier scan",
        "description": "The carrier has not reported a scan for twelve hours.",
        "category": "carrier_issue",
        "status": "open",
        "origin": "customer",
        "branch": "la_office",
    }

    created = client.post("/api/incidents", json=payload)
    assert created.status_code == 201
    incident = created.json()["data"]

    listed = client.get("/api/incidents", params={"status": "open"})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [incident["id"]]

    fetched = client.get(f"/api/incidents/{incident['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["title"] == payload["title"]

    updated = client.patch(
        f"/api/incidents/{incident['id']}/status",
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "in_progress"

    rejected = client.patch(
        f"/api/incidents/{incident['id']}/status",
        json={"status": "open"},
    )
    assert rejected.status_code == 409

    summary = client.get("/api/incidents/summary")
    assert summary.status_code == 200
    assert summary.json()["data"]["by_status"] == {"in_progress": 1}


def test_seed_csv_produces_exact_context_summary(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = tmp_path / "seeded-incidents.db"
    monkeypatch.setenv("INCIDENTS_DB_PATH", str(db_path))
    repo_root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    env["INCIDENTS_DB_PATH"] = str(db_path)

    seeded = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "seed_incidents.py"),
            "--csv-path",
            str(fixture_path),
        ],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert seeded.returncode == 0, seeded.stderr
    summary = client.get("/api/incidents/summary")
    assert summary.status_code == 200
    assert summary.json()["data"]["by_status"] == {
        "open": 29,
        "resolved": 52,
        "discarded": 14,
    }
    assert summary.json()["data"]["by_category"] == {
        "lost_parcel": 14,
        "carrier_issue": 45,
        "delivery_failure": 19,
        "returns_issue": 17,
    }
    assert sum(summary.json()["data"]["by_status"].values()) == 95


def test_knowledge_query_returns_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.run_knowledge_query",
        lambda question: {
            "answer": "The standard return window is 30 calendar days.",
            "sources": [
                {
                    "source_document": "returns-policy",
                    "section": "Standard return window",
                    "language": "en",
                }
            ],
        },
    )

    response = client.post(
        "/knowledge/query",
        json={"question": "What is the standard return window?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("The standard return window")
    assert payload["sources"] == [
        {
            "source_document": "returns-policy",
            "section": "Standard return window",
            "language": "en",
        }
    ]


def test_agent_query_returns_trace_id(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.run_agent_query",
        lambda question, thread_id=None, user_id=None: {
            "answer": "No, standard SLAs do not apply during Black Friday.",
            "sources": [
                {
                    "source_document": "sla-delivery",
                    "section": "High-demand peak dates warning",
                    "language": "en",
                }
            ],
            "trace_id": "trace-123",
            "sources_used": ["mcp_ticket_tool"],
        },
    )

    response = client.post(
        "/agent/query",
        json={"question": "Can we promise 3-5 day SLA during Black Friday?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"] == "trace-123"
    assert payload["sources_used"] == ["mcp_ticket_tool"]
    assert "Black Friday" in payload["answer"] or "SLA" in payload["answer"]
    assert payload["sources"][0]["source_document"] == "sla-delivery"


def test_agent_guardrail_summary_returns_counts(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.guardrail_summary",
        lambda reset=False: {
            "generated_at": "2026-08-08T16:00:00+00:00",
            "by_rule": {"jailbreak_variant_1": 2, "casual_steer_back": 1},
            "by_type": {"security": 2, "content": 1},
            "total": 3,
        },
    )

    response = client.get("/agent/guardrails/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["by_rule"]["jailbreak_variant_1"] == 2
    assert payload["by_type"]["content"] == 1
