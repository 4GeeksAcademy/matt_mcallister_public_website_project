from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
