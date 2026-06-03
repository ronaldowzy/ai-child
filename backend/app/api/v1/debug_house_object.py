from typing import Literal

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import required_auth_account
from app.core.config import get_settings
from app.domain.companion_object import (
    CompanionObjectCreateRequest,
    CompanionObjectSource,
    CompanionObjectType,
    VisualKind,
)
from app.domain.schemas.auth import AuthAccountProfile
from app.domain.schemas.conversation import CompanionObjectMeta
from app.services.companion_object_service import (
    CompanionObjectService,
    get_companion_object_service,
)

router = APIRouter(prefix="/debug/house-object", tags=["debug"])
companion_object_service = get_companion_object_service()


DebugObjectState = Literal["seed", "co_create", "recall"]
DebugLightLocation = Literal["窗边", "地毯边", "小白狐旁边", "窗外"]


class HouseObjectDebugCreateRequest(BaseModel):
    visual_kind: VisualKind
    state: DebugObjectState
    light_location: DebugLightLocation
    name: str = Field(default="调试小客人", min_length=1, max_length=40)


class HouseObjectDebugCreateResponse(BaseModel):
    companion_object: CompanionObjectMeta


class HouseObjectDebugResetResponse(BaseModel):
    retired_count: int


_VISUAL_KIND_TO_OBJECT_TYPE: dict[VisualKind, CompanionObjectType] = {
    VisualKind.STAR: CompanionObjectType.STAR,
    VisualKind.CLOUD: CompanionObjectType.CLOUD,
    VisualKind.PAPER_BOAT: CompanionObjectType.PAPER_BOAT,
    VisualKind.TINY_DOOR: CompanionObjectType.STORY_GATE,
    VisualKind.DINO_SHADOW: CompanionObjectType.DRAWING_CHARACTER,
    VisualKind.BLOCK_LIGHT: CompanionObjectType.BLOCK_MONSTER,
}


@router.post(
    "/create",
    response_model=HouseObjectDebugCreateResponse,
    response_model_exclude_none=True,
)
def create_debug_house_object(
    request: HouseObjectDebugCreateRequest,
    authorization: str | None = Header(default=None),
    debug_token: str | None = Header(
        default=None,
        alias="X-Child-AI-Debug-Token",
    ),
) -> HouseObjectDebugCreateResponse:
    account = _require_debug_access(
        authorization=authorization,
        debug_token=debug_token,
    )
    companion = companion_object_service.create(
        CompanionObjectCreateRequest(
            child_id=account.child_id,
            name=request.name.strip(),
            object_type=_VISUAL_KIND_TO_OBJECT_TYPE[request.visual_kind],
            source_type=CompanionObjectSource.IMAGE_SHARE,
            safe_summary="开发调试创建的小屋小客人",
            light_location=request.light_location,
        )
    )
    return HouseObjectDebugCreateResponse(
        companion_object=_to_debug_meta(companion, request.state),
    )


@router.post(
    "/reset",
    response_model=HouseObjectDebugResetResponse,
)
def reset_debug_house_objects(
    authorization: str | None = Header(default=None),
    debug_token: str | None = Header(
        default=None,
        alias="X-Child-AI-Debug-Token",
    ),
) -> HouseObjectDebugResetResponse:
    account = _require_debug_access(
        authorization=authorization,
        debug_token=debug_token,
    )
    return HouseObjectDebugResetResponse(
        retired_count=companion_object_service.retire_for_child(account.child_id),
    )


def _require_debug_access(
    *,
    authorization: str | None,
    debug_token: str | None,
) -> AuthAccountProfile:
    settings = get_settings()
    if settings.environment.lower() in {"prod", "production", "release"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="debug tools are unavailable",
        )
    if not settings.enable_debug_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="debug tools are disabled",
        )
    if not settings.debug_tools_token or debug_token != settings.debug_tools_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid debug token",
        )
    return required_auth_account(authorization)


def _to_debug_meta(companion, state: DebugObjectState) -> CompanionObjectMeta:
    if state == "seed":
        ui_state = "seed"
        action = "name_seed"
    else:
        ui_state = "active"
        action = state
    return CompanionObjectMeta(
        id=str(companion.id),
        name=companion.name,
        object_type=_enum_value(companion.object_type),
        light_location=companion.light_location,
        state=ui_state,
        action=action,
        visual_kind=_enum_value(companion.visual_kind),
    )


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)
