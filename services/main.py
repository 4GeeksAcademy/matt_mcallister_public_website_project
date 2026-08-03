"""TrackFlow FastAPI application entrypoint."""

from __future__ import annotations

import logging
import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from inventory.router import router as inventory_router
from reporting.router import router as reporting_router
from telemetry.router import router as telemetry_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trackflow")

TELEMETRY_ENDPOINT = os.getenv(
    "TELEMETRY_ENDPOINT",
    "http://127.0.0.1:8000/telemetry/events",
)
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("TELEMETRY_ENDPOINT=%s", TELEMETRY_ENDPOINT)
    logger.info("API ready at %s", API_BASE)
    yield


app = FastAPI(title="TrackFlow Services", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)
app.include_router(inventory_router)
app.include_router(reporting_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
