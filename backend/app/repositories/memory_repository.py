from typing import Protocol

import logging

from app.domain.memory import MemoryItem


logger = logging.getLogger("app.memory_repository")


class MemoryRepositoryUnavailable(RuntimeError):
    pass


class MemoryRepository(Protocol):
    def save(self, memory: MemoryItem) -> MemoryItem:
        ...

    def get(self, memory_id: str) -> MemoryItem | None:
        ...

    def list_by_child(self, child_id: str) -> list[MemoryItem]:
        ...

    def delete(self, memory_id: str) -> bool:
        ...

    def clear(self) -> None:
        ...


class InMemoryMemoryRepository:
    """Process-local memory repository for v0.1 structured memory tests."""

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def save(self, memory: MemoryItem) -> MemoryItem:
        self._items[memory.id] = memory.model_copy(deep=True)
        return self._items[memory.id].model_copy(deep=True)

    def get(self, memory_id: str) -> MemoryItem | None:
        memory = self._items.get(memory_id)
        if memory is None:
            return None
        return memory.model_copy(deep=True)

    def list_by_child(self, child_id: str) -> list[MemoryItem]:
        memories = [
            memory.model_copy(deep=True)
            for memory in self._items.values()
            if memory.child_id == child_id
        ]
        return sorted(memories, key=lambda memory: memory.created_at, reverse=True)

    def delete(self, memory_id: str) -> bool:
        if memory_id not in self._items:
            return False
        del self._items[memory_id]
        return True

    def clear(self) -> None:
        self._items.clear()


_memory_repository = InMemoryMemoryRepository()


def get_memory_repository() -> MemoryRepository:
    return _memory_repository


def configure_default_memory_repository() -> MemoryRepository:
    global _memory_repository
    try:
        from app.repositories.memory_sql_repository import (
            SqlAlchemyMemoryRepository,
        )

        repository = SqlAlchemyMemoryRepository()
        repository.ensure_available()
        _memory_repository = repository
    except Exception as exc:
        logger.warning(
            "memory_repository_fallback",
            extra={
                "event": "memory_repository_fallback",
                "error_type": exc.__class__.__name__,
            },
        )
        _memory_repository = InMemoryMemoryRepository()
    return _memory_repository


configure_default_memory_repository()
