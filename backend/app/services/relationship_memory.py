from collections.abc import Iterable

from app.domain.memory import MemoryItem, MemorySensitivity, MemoryType
from app.services.memory_service import MemoryService


RELATIONSHIP_MEMORY_TYPE_KEY = "relationship_memory_type"
RELATIONSHIP_MEMORY_SOURCE = "conversation_summary"
INTEREST_SEED = "interest_seed"
TOPIC_BOUNDARY = "topic_boundary"
PROUD_MOMENT = "proud_moment"


def relationship_metadata(
    *,
    relationship_memory_type: str,
    topic: str | None = None,
    next_hook: str | None = None,
    do_not_overask: bool = True,
    source: str = RELATIONSHIP_MEMORY_SOURCE,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        RELATIONSHIP_MEMORY_TYPE_KEY: relationship_memory_type,
        "source": source,
        "do_not_overask": do_not_overask,
    }
    if topic:
        metadata["topic"] = topic
    if next_hook:
        metadata["next_hook"] = next_hook
    if extra:
        metadata.update(extra)
    return metadata


def memory_relationship_type(memory: MemoryItem) -> str | None:
    for evidence in memory.evidence:
        value = evidence.metadata.get(RELATIONSHIP_MEMORY_TYPE_KEY)
        if isinstance(value, str):
            return value
    return None


def memory_relationship_topic(memory: MemoryItem) -> str | None:
    for evidence in memory.evidence:
        value = evidence.metadata.get("topic")
        if isinstance(value, str):
            return value
    return None


def memory_relationship_next_hook(memory: MemoryItem) -> str | None:
    for evidence in memory.evidence:
        value = evidence.metadata.get("next_hook")
        if isinstance(value, str):
            return value
    return None


def memory_relationship_metadata(memory: MemoryItem) -> dict[str, object]:
    for evidence in memory.evidence:
        if RELATIONSHIP_MEMORY_TYPE_KEY in evidence.metadata:
            return dict(evidence.metadata)
    return {}


def is_relationship_memory(
    memory: MemoryItem,
    *,
    relationship_memory_type: str | None = None,
) -> bool:
    actual = memory_relationship_type(memory)
    if actual is None:
        return False
    return relationship_memory_type is None or actual == relationship_memory_type


def relationship_memories(
    memories: Iterable[MemoryItem],
    *,
    relationship_memory_type: str | None = None,
) -> list[MemoryItem]:
    return [
        memory
        for memory in memories
        if is_relationship_memory(
            memory,
            relationship_memory_type=relationship_memory_type,
        )
    ]


def latest_interest_seed(
    memory_service: MemoryService,
    *,
    child_id: str,
) -> MemoryItem | None:
    memories = memory_service.list_memories(
        child_id,
        active_only=True,
        include_safety=False,
    )
    candidates = [
        memory
        for memory in memories
        if (
            memory.memory_type == MemoryType.INTEREST
            and memory.sensitivity == MemorySensitivity.LOW
            and is_relationship_memory(memory, relationship_memory_type=INTEREST_SEED)
        )
    ]
    return max(
        candidates,
        key=lambda memory: (
            memory.updated_at,
            memory.created_at,
            memory.importance,
            memory.confidence,
        ),
        default=None,
    )


def latest_relationship_memory(
    memory_service: MemoryService,
    *,
    child_id: str,
    relationship_memory_type: str,
    memory_type: MemoryType | None = None,
) -> MemoryItem | None:
    memories = memory_service.list_memories(
        child_id,
        memory_type=memory_type,
        active_only=True,
        include_safety=False,
    )
    candidates = [
        memory
        for memory in memories
        if is_relationship_memory(
            memory,
            relationship_memory_type=relationship_memory_type,
        )
    ]
    return max(
        candidates,
        key=lambda memory: (
            memory.updated_at,
            memory.created_at,
            memory.importance,
            memory.confidence,
        ),
        default=None,
    )


def latest_topic_boundary(
    memory_service: MemoryService,
    *,
    child_id: str,
) -> MemoryItem | None:
    return latest_relationship_memory(
        memory_service,
        child_id=child_id,
        relationship_memory_type=TOPIC_BOUNDARY,
        memory_type=MemoryType.STRATEGY,
    )
