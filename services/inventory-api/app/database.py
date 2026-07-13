from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from tinydb import TinyDB

from app.core.config import get_settings


@lru_cache
def get_engine():
    database_url = get_settings().database_url
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url)


def get_tinydb_client() -> TinyDB:
    return TinyDB(get_settings().tinydb_path)


def get_tinydb() -> Generator[TinyDB, None, None]:
    yield get_tinydb_client()


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())
