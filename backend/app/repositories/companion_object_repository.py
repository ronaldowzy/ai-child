"""Companion object repository protocol and in-memory implementation."""

from __future__ import annotations

import logging
from typing import Protocol

from app.domain.companion_object import CompanionObject, CompanionObjectStatus

logger = logging.getLogger("app.companion_object_repository")


class CompanionObjectRepositoryUnavailable(RuntimeError):
    pass


class CompanionObjectRepository(Protocol):
    def save(self, companion: CompanionObject) -> CompanionObject:
        ...

    def get(self, companion_id: str) -> CompanionObject | None:
        ...

    def get_active_by_child(self, child_id: str) -> CompanionObject | None:
        ...

    def list_by_child(self, child_id: str) -> list[CompanionObject]:
        ...

    def delete(self, companion_id: str) -> bool:
        ...

    def clear(self) -> None:
        ...


class InMemoryCompanionObjectRepository:
    """Process-local companion object repository for v0.1 tests."""

    def __init__(self) -> None:
        self._items: dict[str, CompanionObject] = {}

    def save(self, companion: CompanionObject) -> CompanionObject:
        self._items[companion.id] = companion.model_copy(deep=True)
        return self._items[companion.id].model_copy(deep=True)

    def get(self, companion_id: str) -> CompanionObject | None:
        item = self._items.get(companion_id)
        return item.model_copy(deep=True) if item else None

    def get_active_by_child(self, child_id: str) -> CompanionObject | None:
        for item in self._items.values():
            if (
                item.child_id == child_id
                and item.status == CompanionObjectStatus.ACTIVE
            ):
                return item.model_copy(deep=True)
        return None

    def list_by_child(self, child_id: str) -> list[CompanionObject]:
        items = [
            item.model_copy(deep=True)
            for item in self._items.values()
            if item.child_id == child_id
        ]
        return sorted(items, key=lambda c: c.created_at, reverse=True)

    def delete(self, companion_id: str) -> bool:
        if companion_id not in self._items:
            return False
        del self._items[companion_id]
        return True

    def clear(self) -> None:
        self._items.clear()


_companion_repository: CompanionObjectRepository = InMemoryCompanionObjectRepository()


def get_companion_object_repository() -> CompanionObjectRepository:
    return _companion_repository


def configure_default_companion_object_repository() -> CompanionObjectRepository:
    global _companion_repository
    try:
        from app.repositories.companion_object_sql_repository import (
            SqlAlchemyCompanionObjectRepository,
        )

        repository = SqlAlchemyCompanionObjectRepository()
        repository.ensure_available()
        _companion_repository = repository
    except Exception as exc:
        logger.warning(
            "companion_object_repository_fallback",
            extra={
                "event": "companion_object_repository_fallback",
                "error_type": exc.__class__.__name__,
            },
        )
        _companion_repository = InMemoryCompanionObjectRepository()
    return _companion_repository


configure_default_companion_object_repository()
