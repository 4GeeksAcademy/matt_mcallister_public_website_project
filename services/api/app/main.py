"""TrackFlow Incident Analysis API."""

from __future__ import annotations

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

app = FastAPI(title="TrackFlow Incident Analysis API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    csv_text = export_result_csv(_last_result)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )


# Backward-compatible aliases used during earlier stubs
@app.post("/analyze")
async def analyze_legacy(file: UploadFile = File(...)) -> dict:
    return await analyze_incidents(file)


@app.post("/export")
async def export_legacy(file: UploadFile = File(...)) -> PlainTextResponse:
    content, filename = await _read_csv_upload(file)
    try:
        result = run_analysis(content, filename)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _store_result(result)
    csv_text = export_result_csv(result)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )
