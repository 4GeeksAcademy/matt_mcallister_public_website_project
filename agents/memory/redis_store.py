"""In-memory and Redis-backed memory stores."""

from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from agents.memory.consolidation import consolidate_entries
from agents.memory.store import MemoryEntry, MemoryProposal

_GLOBAL_MEMORY: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryMemoryStore:
    """Process-local memory store used in tests and local dev."""

    def __init__(self, namespace: str = "default") -> None:
        self._namespace = namespace
        if namespace not in _GLOBAL_MEMORY:
            _GLOBAL_MEMORY[namespace] = {"entries": {}, "pending": {}}
        self._data = _GLOBAL_MEMORY[namespace]

    def read(self, user_id: str) -> list[MemoryEntry]:
        return self.list_entries(user_id)

    def list_entries(self, user_id: str) -> list[MemoryEntry]:
        raw = self._data["entries"].get(user_id, [])
        return [MemoryEntry(**item) for item in raw]

    def get_pending_proposal(self, user_id: str) -> Optional[MemoryProposal]:
        raw = self._data["pending"].get(user_id)
        return MemoryProposal(**raw) if raw else None

    def set_pending_proposal(self, user_id: str, proposal: Optional[MemoryProposal]) -> None:
        if proposal is None:
            self._data["pending"].pop(user_id, None)
        else:
            self._data["pending"][user_id] = proposal.to_dict()

    def commit_entry(self, user_id: str, *, category: str, text: str) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            category=category,
            text=text.strip(),
        )
        entries = self.list_entries(user_id) + [entry]
        consolidated = consolidate_entries([e.to_dict() for e in entries])
        self.replace_entries(user_id, [MemoryEntry(**item) for item in consolidated])
        return entry

    def replace_entries(self, user_id: str, entries: list[MemoryEntry]) -> None:
        self._data["entries"][user_id] = [entry.to_dict() for entry in entries]


class RedisMemoryStore:
    """Redis-backed memory store for persistent user preferences."""

    def __init__(self, redis_url: str, *, prefix: str = "trackflow:agent-memory") -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = prefix

    def _entries_key(self, user_id: str) -> str:
        return f"{self._prefix}:entries:{user_id}"

    def _pending_key(self, user_id: str) -> str:
        return f"{self._prefix}:pending:{user_id}"

    def read(self, user_id: str) -> list[MemoryEntry]:
        return self.list_entries(user_id)

    def list_entries(self, user_id: str) -> list[MemoryEntry]:
        raw = self._client.get(self._entries_key(user_id))
        if not raw:
            return []
        items = json.loads(raw)
        return [MemoryEntry(**item) for item in items]

    def get_pending_proposal(self, user_id: str) -> Optional[MemoryProposal]:
        raw = self._client.get(self._pending_key(user_id))
        return MemoryProposal(**json.loads(raw)) if raw else None

    def set_pending_proposal(self, user_id: str, proposal: Optional[MemoryProposal]) -> None:
        key = self._pending_key(user_id)
        if proposal is None:
            self._client.delete(key)
        else:
            self._client.set(key, json.dumps(proposal.to_dict()))

    def commit_entry(self, user_id: str, *, category: str, text: str) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            category=category,
            text=text.strip(),
        )
        entries = self.list_entries(user_id) + [entry]
        consolidated = consolidate_entries([e.to_dict() for e in entries])
        self.replace_entries(user_id, [MemoryEntry(**item) for item in consolidated])
        return entry

    def replace_entries(self, user_id: str, entries: list[MemoryEntry]) -> None:
        self._client.set(
            self._entries_key(user_id),
            json.dumps([entry.to_dict() for entry in entries]),
        )


def get_memory_store() -> InMemoryMemoryStore | RedisMemoryStore:
    backend = os.environ.get("AGENT_MEMORY_BACKEND", "memory").lower()
    if backend == "redis":
        url = os.environ.get("AGENT_MEMORY_REDIS_URL") or os.environ.get("REDIS_URL")
        if not url:
            raise RuntimeError("AGENT_MEMORY_BACKEND=redis requires REDIS_URL")
        # Use db 1 when default redis://localhost:6379/0 to avoid Celery key collisions.
        if url.endswith("/0"):
            url = url[:-1] + "1"
        return RedisMemoryStore(url)
    namespace = os.environ.get("AGENT_MEMORY_NAMESPACE", "default")
    return InMemoryMemoryStore(namespace=namespace)


def reset_memory_store(namespace: str = "default") -> None:
    _GLOBAL_MEMORY.pop(namespace, None)
