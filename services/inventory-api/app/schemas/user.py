from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = ""
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = None


class UserNameUpdate(BaseModel):
    name: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=8)


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}
