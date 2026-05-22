from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import logging
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
    MemoryUpdateRequest,
)
from app.repositories.memory_repository import (
    InMemoryMemoryRepository,
    MemoryRepository,
    MemoryRepositoryUnavailable,
    get_memory_repository,
)


class MemoryServiceError(RuntimeError):
    pass


class MemoryNotFoundError(MemoryServiceError):
    pass


class UnsafeMemoryError(MemoryServiceError):
    pass


logger = logging.getLogger("app.memory_service")


class MemoryService:
    def __init__(
        self,
        *,
        repository: MemoryRepository | None = None,
        fallback_repository: InMemoryMemoryRepository | None = None,
        now_provider: Callable[[], datetime] | None = None,
        fallback_to_memory: bool = True,
    ) -> None:
        self._repository = repository or get_memory_repository()
        self._fallback_repository = fallback_repository or InMemoryMemoryRepository()
        self._fallback_to_memory = fallback_to_memory
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def create(self, request: MemoryCreateRequest) -> MemoryItem:
        now = self._now()
        expires_at = request.expires_at or self._default_expires_at(
            request.memory_type, now
        )
        memory = MemoryItem(
            id=str(uuid4()),
            child_id=request.child_id,
            memory_type=request.memory_type,
            content=request.content,
            tags=request.tags,
            evidence=request.evidence,
            confidence=request.confidence,
            importance=request.importance,
            sensitivity=request.sensitivity,
            visible_to_parent=request.visible_to_parent,
            visible_to_child=request.visible_to_child,
            requires_parent_attention=request.requires_parent_attention,
            expires_at=expires_at,
            embedding_id=request.embedding_id,
            created_at=now,
            updated_at=now,
        )
        memory = self._normalize_safety_fields(memory)
        self._validate_memory_for_storage(memory)
        return self._save(memory)

    def create_many(self, requests: list[MemoryCreateRequest]) -> list[MemoryItem]:
        return [self.create(request) for request in requests]

    def list_memories(
        self,
        child_id: str,
        *,
        memory_type: MemoryType | None = None,
        active_only: bool = True,
        include_safety: bool = True,
    ) -> list[MemoryItem]:
        memories = self._list_by_child(child_id)
        return [
            memory
            for memory in memories
            if (memory_type is None or memory.memory_type == memory_type)
            and (include_safety or memory.memory_type != MemoryType.SAFETY)
            and (not active_only or not self._is_expired(memory))
        ]

    def retrieve(
        self,
        child_id: str,
        *,
        query: str | None = None,
        memory_types: list[MemoryType] | None = None,
        limit: int = 10,
        include_safety: bool = False,
    ) -> list[MemoryItem]:
        memories = self.list_memories(
            child_id,
            active_only=True,
            include_safety=include_safety,
        )
        if memory_types is not None:
            allowed_types = set(memory_types)
            memories = [
                memory for memory in memories if memory.memory_type in allowed_types
            ]

        scored = [
            (self._score(memory, query), memory)
            for memory in memories
            if self._matches_query(memory, query)
        ]
        scored.sort(
            key=lambda item: (
                item[0],
                item[1].importance,
                item[1].confidence,
                item[1].updated_at,
            ),
            reverse=True,
        )
        return [memory for _, memory in scored[: max(limit, 0)]]

    def update(self, memory_id: str, request: MemoryUpdateRequest) -> MemoryItem:
        current = self._get(memory_id)
        if current is None:
            raise MemoryNotFoundError(f"Memory {memory_id} was not found")

        updates = {
            field_name: getattr(request, field_name)
            for field_name in request.model_fields_set
        }
        updated = current.model_copy(
            update={**updates, "updated_at": self._now()},
            deep=True,
        )
        updated = self._normalize_safety_fields(updated)
        self._validate_memory_for_storage(updated)
        return self._save(updated)

    def delete(self, memory_id: str) -> bool:
        try:
            return self._repository.delete(memory_id)
        except (MemoryRepositoryUnavailable, SQLAlchemyError) as exc:
            self._log_repository_fallback(
                operation="delete",
                error_type=exc.__class__.__name__,
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.delete(memory_id)

    def get(self, memory_id: str) -> MemoryItem:
        memory = self._get(memory_id)
        if memory is None:
            raise MemoryNotFoundError(f"Memory {memory_id} was not found")
        return memory

    def _save(self, memory: MemoryItem) -> MemoryItem:
        try:
            return self._repository.save(memory)
        except (MemoryRepositoryUnavailable, SQLAlchemyError) as exc:
            self._log_repository_fallback(
                operation="save",
                error_type=exc.__class__.__name__,
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.save(memory)

    def _get(self, memory_id: str) -> MemoryItem | None:
        try:
            return self._repository.get(memory_id)
        except (MemoryRepositoryUnavailable, SQLAlchemyError) as exc:
            self._log_repository_fallback(
                operation="get",
                error_type=exc.__class__.__name__,
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.get(memory_id)

    def _list_by_child(self, child_id: str) -> list[MemoryItem]:
        try:
            return self._repository.list_by_child(child_id)
        except (MemoryRepositoryUnavailable, SQLAlchemyError) as exc:
            self._log_repository_fallback(
                operation="list_by_child",
                error_type=exc.__class__.__name__,
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.list_by_child(child_id)

    def _log_repository_fallback(self, *, operation: str, error_type: str) -> None:
        logger.warning(
            "memory_repository_fallback",
            extra={
                "event": "memory_repository_fallback",
                "operation": operation,
                "error_type": error_type,
            },
        )

    def _now(self) -> datetime:
        now = self._now_provider()
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now

    def _default_expires_at(
        self, memory_type: MemoryType, created_at: datetime
    ) -> datetime | None:
        ttl_days = {
            MemoryType.INTEREST: 180,
            MemoryType.LEARNING_PATTERN: 90,
            MemoryType.EXPRESSION_PATTERN: 60,
            MemoryType.EMOTION_OBSERVATION: 14,
            MemoryType.EVENT: 30,
            MemoryType.STRATEGY: 90,
        }.get(memory_type)
        if ttl_days is None:
            return None
        return created_at + timedelta(days=ttl_days)

    def _is_expired(self, memory: MemoryItem) -> bool:
        return memory.expires_at is not None and memory.expires_at <= self._now()

    def _normalize_safety_fields(self, memory: MemoryItem) -> MemoryItem:
        if (
            memory.memory_type == MemoryType.SAFETY
            or memory.sensitivity == MemorySensitivity.CRITICAL
        ):
            sensitivity = (
                MemorySensitivity.CRITICAL
                if memory.sensitivity == MemorySensitivity.CRITICAL
                else MemorySensitivity.HIGH
            )
            return memory.model_copy(
                update={
                    "sensitivity": sensitivity,
                    "visible_to_parent": True,
                    "requires_parent_attention": True,
                },
                deep=True,
            )
        return memory

    def _validate_memory_for_storage(self, memory: MemoryItem) -> None:
        forbidden_sources = {
            "raw_audio",
            "original_audio",
            "raw_photo",
            "original_photo",
            "raw_image",
            "original_image",
            "raw_chat",
            "full_chat",
            "chat_transcript",
            "long_chat_transcript",
        }
        for evidence in memory.evidence:
            source = evidence.source.strip().lower()
            if source in forbidden_sources:
                raise UnsafeMemoryError(
                    "Long-term memory must use structured summaries, not raw media or full transcripts"
                )

        forbidden_content_markers = (
            "孩子胆小",
            "孩子不合群",
            "孩子懒",
            "孩子不聪明",
            "内向是缺陷",
            "内向不好",
            "内向有问题",
        )
        if any(marker in memory.content for marker in forbidden_content_markers):
            raise UnsafeMemoryError(
                "Memory content must use observational language without fixed negative labels"
            )

    def _matches_query(self, memory: MemoryItem, query: str | None) -> bool:
        if not query:
            return True
        normalized_query = query.strip().lower()
        if not normalized_query:
            return True
        haystack = " ".join(
            [
                memory.content,
                memory.memory_type.value,
                *memory.tags,
            ]
        ).lower()
        if any(token in haystack for token in normalized_query.split()):
            return True
        return any(
            tag.lower() and tag.lower() in normalized_query for tag in memory.tags
        )

    def _score(self, memory: MemoryItem, query: str | None) -> float:
        if not query:
            return memory.importance + memory.confidence
        normalized_query = query.strip().lower()
        score = memory.importance + memory.confidence
        for tag in memory.tags:
            if tag.lower() in normalized_query:
                score += 1.0
        if normalized_query and normalized_query in memory.content.lower():
            score += 0.5
        return score


_memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    return _memory_service
