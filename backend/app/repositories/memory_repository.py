from app.domain.memory import MemoryItem


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


def get_memory_repository() -> InMemoryMemoryRepository:
    return _memory_repository
