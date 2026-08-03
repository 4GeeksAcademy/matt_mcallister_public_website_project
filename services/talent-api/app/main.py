from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query as QueryParam, status
from fastapi.middleware.cors import CORSMiddleware
from tinydb import Query, TinyDB

from app.models import (
    CandidateCreate,
    CandidateOut,
    CandidatePage,
    CandidatePatch,
    CandidateStage,
    CandidateStatus,
    NoteCreate,
    NoteOut,
    utc_now,
)
from app.store import candidate_table, find_candidate, find_note, get_database, note_table


API_PREFIX = "/tracker/api/v1"
app = FastAPI(title="TrackFlow Talent API", version="1.0.0")

default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
]
configured_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins or default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def database() -> Iterator[TinyDB]:
    db = get_database()
    try:
        yield db
    finally:
        db.close()


def require_candidate(db: TinyDB, candidate_id: str) -> dict:
    candidate = find_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


def candidate_response(db: TinyDB, candidate: dict) -> CandidateOut:
    note = Query()
    return CandidateOut(
        **candidate,
        notes_count=len(note_table(db).search(note.candidate_id == candidate["id"])),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{API_PREFIX}/records", response_model=CandidatePage)
def list_candidates(
    candidate_status: CandidateStatus | None = QueryParam(default=None, alias="status"),
    stage: CandidateStage | None = None,
    search: str | None = None,
    page: int = QueryParam(default=1, ge=1),
    limit: int = QueryParam(default=20, ge=1, le=100),
    db: TinyDB = Depends(database),
) -> CandidatePage:
    candidates = list(candidate_table(db).all())
    if candidate_status is not None:
        candidates = [
            item for item in candidates if item["status"] == candidate_status.value
        ]
    if stage is not None:
        candidates = [item for item in candidates if item["stage"] == stage.value]
    if search and search.strip():
        needle = search.strip().casefold()
        candidates = [
            item
            for item in candidates
            if needle
            in " ".join(
                [item["full_name"], item["email"], item["position"]]
            ).casefold()
        ]

    candidates.sort(key=lambda item: item["applied_at"], reverse=True)
    total = len(candidates)
    start = (page - 1) * limit
    selected = candidates[start : start + limit]
    return CandidatePage(
        total=total,
        page=page,
        limit=limit,
        data=[candidate_response(db, item) for item in selected],
    )


@app.get(f"{API_PREFIX}/records/{{candidate_id}}", response_model=CandidateOut)
def get_candidate(
    candidate_id: str, db: TinyDB = Depends(database)
) -> CandidateOut:
    return candidate_response(db, require_candidate(db, candidate_id))


@app.post(
    f"{API_PREFIX}/records",
    response_model=CandidateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate(
    payload: CandidateCreate, db: TinyDB = Depends(database)
) -> CandidateOut:
    candidate = Query()
    if candidate_table(db).contains(candidate.email == str(payload.email)):
        raise HTTPException(status_code=409, detail="A candidate with this email exists")

    now = utc_now()
    record = {
        "id": str(uuid4()),
        **payload.model_dump(mode="json"),
        "status": CandidateStatus.RECEIVED.value,
        "stage": CandidateStage.PENDING.value,
        "applied_at": now,
        "updated_at": now,
    }
    candidate_table(db).insert(record)
    return candidate_response(db, record)


@app.put(f"{API_PREFIX}/records/{{candidate_id}}", response_model=CandidateOut)
def replace_candidate(
    candidate_id: str,
    payload: CandidateCreate,
    db: TinyDB = Depends(database),
) -> CandidateOut:
    current = require_candidate(db, candidate_id)
    replacement = {
        **current,
        **payload.model_dump(mode="json"),
        "updated_at": utc_now(),
    }
    candidate_table(db).update(replacement, Query().id == candidate_id)
    return candidate_response(db, replacement)


@app.patch(f"{API_PREFIX}/records/{{candidate_id}}", response_model=CandidateOut)
def patch_candidate(
    candidate_id: str,
    payload: CandidatePatch,
    db: TinyDB = Depends(database),
) -> CandidateOut:
    current = require_candidate(db, candidate_id)
    changes = payload.model_dump(mode="json", exclude_none=True)
    updated = {**current, **changes, "updated_at": utc_now()}
    candidate_table(db).update(updated, Query().id == candidate_id)
    return candidate_response(db, updated)


@app.delete(
    f"{API_PREFIX}/records/{{candidate_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_candidate(candidate_id: str, db: TinyDB = Depends(database)) -> None:
    require_candidate(db, candidate_id)
    candidate_table(db).remove(Query().id == candidate_id)
    note_table(db).remove(Query().candidate_id == candidate_id)


@app.get(
    f"{API_PREFIX}/records/{{candidate_id}}/notes",
    response_model=list[NoteOut],
)
def list_notes(candidate_id: str, db: TinyDB = Depends(database)) -> list[NoteOut]:
    require_candidate(db, candidate_id)
    notes = note_table(db).search(Query().candidate_id == candidate_id)
    notes.sort(key=lambda item: item["created_at"], reverse=True)
    return [NoteOut(**item) for item in notes]


@app.post(
    f"{API_PREFIX}/records/{{candidate_id}}/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    candidate_id: str,
    payload: NoteCreate,
    db: TinyDB = Depends(database),
) -> NoteOut:
    require_candidate(db, candidate_id)
    record = {
        "id": str(uuid4()),
        "candidate_id": candidate_id,
        "content": payload.content.strip(),
        "created_at": utc_now(),
    }
    note_table(db).insert(record)
    return NoteOut(**record)


@app.delete(
    f"{API_PREFIX}/records/{{candidate_id}}/notes/{{note_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_note(
    candidate_id: str, note_id: str, db: TinyDB = Depends(database)
) -> None:
    require_candidate(db, candidate_id)
    if find_note(db, candidate_id, note_id) is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note = Query()
    note_table(db).remove(
        (note.id == note_id) & (note.candidate_id == candidate_id)
    )
