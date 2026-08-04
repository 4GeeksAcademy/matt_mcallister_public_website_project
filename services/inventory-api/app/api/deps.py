from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from tinydb import TinyDB

from app.core.security import decode_token
from app.database import get_tinydb
from app.models.user import User
from app.services.user_service import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_token_subject(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        subject = decode_token(token).get("sub")
    except JWTError:
        raise credentials_exception
    if not isinstance(subject, str) or not subject:
        raise credentials_exception
    return subject


def get_current_user(
    subject: str = Depends(get_token_subject), db: TinyDB = Depends(get_tinydb)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = get_user_by_email(db, subject)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_self_or_admin(current_user: User, target_user_id: int) -> None:
    if current_user.id != target_user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
