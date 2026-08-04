"""TrackFlow Incident Analysis API."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.analysis_bridge import (
    AnalysisError,
    AnalysisResult,
    export_result_csv,
    result_to_dict,
    run_analysis,
)

# Repo root so `services.celery_app` and `data.*` imports resolve from this service.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.knowledge_bridge import (  # noqa: E402
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    run_knowledge_query,
)
from app.agent_bridge import (  # noqa: E402
    AgentQueryRequest,
    AgentQueryResponse,
    run_agent_query,
)
from app.incidents import router as incidents_router  # noqa: E402
from services.celery_app.celery import app as celery_app  # noqa: E402
from services.celery_app.tasks import analyze_incident  # noqa: E402

app = FastAPI(title="TrackFlow API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(incidents_router)

_last_result: AnalysisResult | None = None


def _store_result(result: AnalysisResult) -> AnalysisResult:
    global _last_result
    _last_result = result
    return result


async def _read_csv_upload(file: UploadFile) -> tuple[str, str]:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="CSV must be UTF-8 encoded."
        ) from exc

    return content, filename


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/incidents/analyze")
async def analyze_incidents(file: UploadFile = File(...)) -> dict:
    content, filename = await _read_csv_upload(file)
    try:
        result = run_analysis(content, filename)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _store_result(result)
    return result_to_dict(result)


@app.get("/api/incidents/results/export")
def export_last_results() -> PlainTextResponse:
    if _last_result is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis results available. Upload a CSV to /api/incidents/analyze first.",
        )
    return PlainTextResponse(
        export_result_csv(_last_result),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )


@app.post("/knowledge/query", response_model=KnowledgeQueryResponse)
def knowledge_query(body: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
    """Answer commercial knowledge questions via the RAG pipeline."""
    try:
        result = run_knowledge_query(body.question.strip())
    except Exception as exc:  # noqa: BLE001 — surface as 502 for client UX
        raise HTTPException(
            status_code=502,
            detail="Knowledge query failed. Please try again shortly.",
        ) from exc
    return KnowledgeQueryResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
    )


@app.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(body: AgentQueryRequest) -> AgentQueryResponse:
    """Answer commercial knowledge questions via the LangGraph support agent."""
    try:
        result = run_agent_query(body.question.strip(), thread_id=body.thread_id)
    except Exception as exc:  # noqa: BLE001 — surface as 502 for client UX
        raise HTTPException(
            status_code=502,
            detail="Agent query failed. Please try again shortly.",
        ) from exc
    return AgentQueryResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        trace_id=result["trace_id"],
    )


@app.post("/export")
async def export(file: UploadFile = File(...)) -> PlainTextResponse:
    content, filename = await _read_csv_upload(file)
    try:
        result = run_analysis(content, filename)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _store_result(result)
    return PlainTextResponse(
        export_result_csv(result),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )


# Backward-compatible aliases used during earlier stubs
@app.post("/analyze")
async def analyze_legacy(file: UploadFile = File(...)) -> dict:
    return await analyze_incidents(file)
