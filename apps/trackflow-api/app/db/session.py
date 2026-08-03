from collections.abc import Generator

from tinydb import TinyDB

from app.core.config import get_settings

settings = get_settings()
db = TinyDB(settings.database_path)


def get_db() -> Generator[TinyDB, None, None]:
    yield db
