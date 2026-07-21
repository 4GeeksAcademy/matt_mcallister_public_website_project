"""Celery application: Redis broker and result backend."""

from __future__ import annotations

import os

from celery import Celery


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError(
            "REDIS_URL is not set. Export a Redis connection string before starting "
            "the API or Celery worker."
        )
    return url


app = Celery(
    "trackflow",
    broker=_redis_url(),
    backend=_redis_url(),
    include=["services.celery_app.tasks"],
)

app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
