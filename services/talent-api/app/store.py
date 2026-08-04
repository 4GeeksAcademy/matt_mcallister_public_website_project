from __future__ import annotations

import os
from pathlib import Path

from tinydb import Query, TinyDB


def database_path() -> Path:
    configured = os.environ.get("TALENT_DB_PATH", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "talent.json"


def get_database() -> TinyDB:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(path)


def candidate_table(db: TinyDB):
    return db.table("candidates")


def note_table(db: TinyDB):
    return db.table("notes")


def find_candidate(db: TinyDB, candidate_id: str) -> dict | None:
    return candidate_table(db).get(Query().id == candidate_id)


def find_note(db: TinyDB, candidate_id: str, note_id: str) -> dict | None:
    note = Query()
    return note_table(db).get(
        (note.id == note_id) & (note.candidate_id == candidate_id)
    )
