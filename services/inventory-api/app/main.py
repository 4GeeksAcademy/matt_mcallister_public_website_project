from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models import inventory  # noqa: F401 — register SQLModel tables
from app.api.router import api_router
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="TrackFlow Inventory API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
