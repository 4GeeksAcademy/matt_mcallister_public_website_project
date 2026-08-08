"""Agent memory models and store protocol."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Protocol


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryEntry:
    id: str
    user_id: str
    category: str
    text: str
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "text": self.text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MemoryProposal:
    id: str
    user_id: str
    category: str
    text: str
    reason: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "text": self.text,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def create(cls, *, user_id: str, category: str, text: str, reason: str) -> "MemoryProposal":
        return cls(
            id=f"prop_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            category=category,
            text=text,
            reason=reason,
        )


class MemoryStore(Protocol):
    def read(self, user_id: str) -> list[MemoryEntry]: ...

    def list_entries(self, user_id: str) -> list[MemoryEntry]: ...

    def get_pending_proposal(self, user_id: str) -> Optional[MemoryProposal]: ...

    def set_pending_proposal(self, user_id: str, proposal: Optional[MemoryProposal]) -> None: ...

    def commit_entry(self, user_id: str, *, category: str, text: str) -> MemoryEntry: ...

    def replace_entries(self, user_id: str, entries: list[MemoryEntry]) -> None: ...
