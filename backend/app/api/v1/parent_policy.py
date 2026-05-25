from fastapi import APIRouter, Header, Query

from app.api.v1.auth import optional_auth_account
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
    authorization: str | None = Header(default=None),
) -> ParentPolicyResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        child_id = account.child_id
    return parent_policy_service.get_policy(child_id)


@router.get("/policy/{child_id}", response_model=ParentPolicyResponse)
def get_parent_policy_by_child(
    child_id: str,
    authorization: str | None = Header(default=None),
) -> ParentPolicyResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        child_id = account.child_id
    return parent_policy_service.get_policy(child_id)


@router.post("/policy", response_model=ParentPolicyResponse)
def update_parent_policy(
    request: ParentPolicyUpdateRequest,
    authorization: str | None = Header(default=None),
) -> ParentPolicyResponse:
    account = optional_auth_account(authorization)
    if account is not None:
        request = request.model_copy(update={"child_id": account.child_id})
    return parent_policy_service.update_policy(request)
