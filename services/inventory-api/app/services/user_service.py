from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from tinydb import Query, TinyDB

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


USERS_TABLE = "users"


def _to_user(doc_id: int, data: dict) -> User:
    return User(
        id=doc_id,
        name=data.get("name", ""),
        email=data["email"],
        hashed_password=data["hashed_password"],
        is_active=data.get("is_active", True),
        is_admin=data.get("is_admin", False),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def get_user_by_id(db: TinyDB, user_id: int) -> Optional[User]:
    table = db.table(USERS_TABLE)
    data = table.get(doc_id=user_id)
    if data is None:
        return None
    return _to_user(user_id, data)


def get_user_by_email(db: TinyDB, email: str) -> Optional[User]:
    table = db.table(USERS_TABLE)
    user_query = Query()
    doc = table.get(user_query.email == email)
    if doc is None:
        return None
    return _to_user(doc.doc_id, dict(doc))


def list_users(db: TinyDB) -> List[User]:
    table = db.table(USERS_TABLE)
    return [_to_user(doc.doc_id, dict(doc)) for doc in table]


def create_user(db: TinyDB, payload: UserCreate) -> User:
    table = db.table(USERS_TABLE)
    now = datetime.now(timezone.utc).isoformat()
    doc_id = table.insert(
        {
            "name": payload.name,
            "email": str(payload.email),
            "hashed_password": hash_password(payload.password),
            "is_active": True,
            "is_admin": False,
            "created_at": now,
        }
    )
    data = table.get(doc_id=doc_id)
    return _to_user(doc_id, data)


def update_user(db: TinyDB, user: User, payload: UserUpdate) -> User:
    table = db.table(USERS_TABLE)
    updates: dict = {}
    if payload.email is not None:
        updates["email"] = str(payload.email)
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.password is not None:
        updates["hashed_password"] = hash_password(payload.password)
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active

    if updates:
        table.update(updates, doc_ids=[user.id])

    refreshed = table.get(doc_id=user.id)
    return _to_user(user.id, refreshed)


def change_password(db: TinyDB, user: User, current_password: str, new_password: str) -> bool:
    if not verify_password(current_password, user.hashed_password):
        return False

    table = db.table(USERS_TABLE)
    table.update(
        {"hashed_password": hash_password(new_password)},
        doc_ids=[user.id],
    )
    return True


def delete_user(db: TinyDB, user: User) -> None:
    table = db.table(USERS_TABLE)
    table.remove(doc_ids=[user.id])
