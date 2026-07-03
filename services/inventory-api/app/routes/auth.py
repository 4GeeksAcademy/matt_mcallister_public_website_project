from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from tinydb import TinyDB

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_tinydb
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, get_user_by_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: TinyDB = Depends(get_tinydb)) -> Token:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return Token(token=create_access_token(user.email))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: TinyDB = Depends(get_tinydb)) -> Token:
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = create_user(db, payload)
    return Token(token=create_access_token(user.email))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
