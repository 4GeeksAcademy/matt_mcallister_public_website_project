import os
import sys
from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.analysis_bridge import export_result_csv, run_analysis

# Repo root so `services.celery_app` and `data.*` imports resolve when uvicorn runs from services/api.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.knowledge_bridge import (  # noqa: E402
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    run_knowledge_query,
)
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _upload_dir() -> Path:
    path = Path(os.environ.get("UPLOAD_DIR", "/data/uploads"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    raw = await file.read()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc

    upload_id = str(uuid4())
    dest = _upload_dir() / f"{upload_id}.csv"
    dest.write_bytes(raw)

    async_result = analyze_incident.delay(upload_id, file.filename)
    return JSONResponse(
        status_code=202,
        content={"task_id": async_result.id},
    )


@app.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    result = AsyncResult(task_id, app=celery_app)
    status = (result.state or "PENDING").lower()
    payload: dict = {
        "task_id": task_id,
        "status": status,
        "result": None,
    }
    if result.successful():
        payload["result"] = result.result
    elif result.failed():
        payload["result"] = str(result.result)
    return payload


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
    return KnowledgeQueryResponse(answer=result["answer"])


@app.post("/export")
async def export(file: UploadFile = File(...)) -> PlainTextResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc

    analysis = run_analysis(content, file.filename)
    csv_text = export_result_csv(analysis)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="incident_analysis_report.csv"'},
    )
