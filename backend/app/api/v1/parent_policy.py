from fastapi import APIRouter, Query

from app.domain.schemas.parent_policy import (
    ParentPolicyResponse,
    ParentPolicyUpdateRequest,
)
from app.services.parent_policy_service import get_parent_policy_service

router = APIRouter(prefix="/parent", tags=["parent"])
parent_policy_service = get_parent_policy_service()


@router.get("/policy", response_model=ParentPolicyResponse)
def get_parent_policy(
    child_id: str = Query("child_default", min_length=1),
) -> ParentPolicyResponse:
    return parent_policy_service.get_policy(child_id)


@router.get("/policy/{child_id}", response_model=ParentPolicyResponse)
def get_parent_policy_by_child(child_id: str) -> ParentPolicyResponse:
    return parent_policy_service.get_policy(child_id)


@router.post("/policy", response_model=ParentPolicyResponse)
def update_parent_policy(
    request: ParentPolicyUpdateRequest,
) -> ParentPolicyResponse:
    return parent_policy_service.update_policy(request)
