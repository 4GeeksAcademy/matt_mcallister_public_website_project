from fastapi import APIRouter, Depends, HTTPException, status
from tinydb import TinyDB

from app.api.deps import get_current_user, require_self_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_public(payload: UserCreate, db: TinyDB = Depends(get_db)) -> UserRead:
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = create_user(db, payload)
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
def get_users(
    db: TinyDB = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[UserRead]:
    _ = current_user
    return [UserRead.model_validate(item) for item in list_users(db)]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: TinyDB = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    _ = current_user
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.put("/{user_id}", response_model=UserRead)
def put_user(
    user_id: int,
    payload: UserUpdate,
    db: TinyDB = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    require_self_or_admin(current_user, user.id)
    if payload.email and payload.email != user.email and get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    updated = update_user(db, user, payload)
    return UserRead.model_validate(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: int,
    db: TinyDB = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    require_self_or_admin(current_user, user.id)
    delete_user(db, user)
