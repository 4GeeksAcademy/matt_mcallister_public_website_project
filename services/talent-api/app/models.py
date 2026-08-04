from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CandidateStatus(str, Enum):
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    SELECTED = "selected"
    DISCARDED = "discarded"


class CandidateStage(str, Enum):
    PENDING = "pending"
    REVIEW = "review"
    PERSONAL_INTERVIEW = "personal_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    OFFER_PRESENTED = "offer_presented"


class CandidateCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=3, max_length=40)
    position: str = Field(min_length=1, max_length=120)
    experience_years: int = Field(ge=0, le=80)
    linkedin_url: HttpUrl | None = None
    cv_url: HttpUrl | None = None


class CandidatePatch(BaseModel):
    status: CandidateStatus | None = None
    stage: CandidateStage | None = None

    @model_validator(mode="after")
    def require_change(self) -> "CandidatePatch":
        if self.status is None and self.stage is None:
            raise ValueError("At least one of status or stage is required")
        return self


class CandidateOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: str
    position: str
    linkedin_url: str | None
    cv_url: str | None
    status: CandidateStatus
    stage: CandidateStage
    experience_years: int
    notes_count: int
    applied_at: str
    updated_at: str


class CandidatePage(BaseModel):
    total: int
    page: int
    limit: int
    data: list[CandidateOut]


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class NoteOut(BaseModel):
    id: str
    candidate_id: str
    content: str
    created_at: str
