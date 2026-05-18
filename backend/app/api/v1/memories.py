from fastapi import APIRouter, HTTPException, Query, status

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryDeleteResponse,
    MemoryItem,
    MemoryType,
    MemoryUpdateRequest,
)
from app.services.memory_service import (
    MemoryNotFoundError,
    MemoryService,
    UnsafeMemoryError,
    get_memory_service,
)

router = APIRouter(prefix="/memories", tags=["memories"])
memory_service: MemoryService = get_memory_service()


@router.post("", response_model=MemoryItem, status_code=status.HTTP_201_CREATED)
def create_memory(request: MemoryCreateRequest) -> MemoryItem:
    try:
        return memory_service.create(request)
    except UnsafeMemoryError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/{child_id}", response_model=list[MemoryItem])
def list_memories(
    child_id: str,
    memory_type: MemoryType | None = Query(default=None, alias="type"),
    active: bool = Query(default=True),
    include_safety: bool = Query(default=True),
) -> list[MemoryItem]:
    return memory_service.list_memories(
        child_id,
        memory_type=memory_type,
        active_only=active,
        include_safety=include_safety,
    )


@router.patch("/{memory_id}", response_model=MemoryItem)
def update_memory(memory_id: str, request: MemoryUpdateRequest) -> MemoryItem:
    try:
        return memory_service.update(memory_id, request)
    except MemoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnsafeMemoryError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
def delete_memory(memory_id: str) -> MemoryDeleteResponse:
    deleted = memory_service.delete(memory_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} was not found",
        )
    return MemoryDeleteResponse(deleted=True)
