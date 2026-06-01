"""Companion object (小屋小客人) domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CompanionObjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


class CompanionObjectType(StrEnum):
    STAR = "star"
    CLOUD = "cloud"
    DRAWING_CHARACTER = "drawing_character"
    TOY_CHARACTER = "toy_character"
    BLOCK_MONSTER = "block_monster"
    PAPER_BOAT = "paper_boat"
    WINDOW_BIRD = "window_bird"
    STORY_GATE = "story_gate"
    OTHER = "other"


class CompanionObjectSource(StrEnum):
    FIRST_OPEN = "first_open"
    IMAGE_SHARE = "image_share"
    CHAT_STORY = "chat_story"
    STORY_CHAIN = "story_chain"


class VisualKind(StrEnum):
    """小物件影子类型，首版 6 种。"""
    STAR = "star"
    CLOUD = "cloud"
    PAPER_BOAT = "paper_boat"
    TINY_DOOR = "tiny_door"
    DINO_SHADOW = "dino_shadow"
    BLOCK_LIGHT = "block_light"


LIGHT_LOCATIONS: tuple[str, ...] = ("窗边", "地毯边", "小白狐旁边", "窗外")

EXCITING_TYPES: frozenset[CompanionObjectType] = frozenset(
    {
        CompanionObjectType.STORY_GATE,
        CompanionObjectType.BLOCK_MONSTER,
    }
)

FORBIDDEN_SUMMARY_MARKERS: tuple[str, ...] = (
    # 隐私
    "地址",
    "学校",
    "班级",
    "电话",
    "真实姓名",
    "校服",
    "校徽",
    # 负面事件
    "吵架",
    "批评",
    "打架",
    "受伤",
    "被骂",
    "冲突",
    # 负面情绪原文
    "哭了",
    "害怕了",
    "生气了",
    "很烦",
    "好累",
    # 学习
    "题目",
    "答案",
    "作业",
    "考试",
    # 保密
    "保密",
    "秘密",
    "隐瞒",
    "不要告诉",
)

SAFE_SUMMARY_MAX_LENGTH = 200
NAME_MAX_LENGTH = 80

# object_type -> visual_kind 确定性映射
_OBJECT_TYPE_TO_VISUAL_KIND: dict[CompanionObjectType, VisualKind] = {
    CompanionObjectType.STAR: VisualKind.STAR,
    CompanionObjectType.CLOUD: VisualKind.CLOUD,
    CompanionObjectType.PAPER_BOAT: VisualKind.PAPER_BOAT,
    CompanionObjectType.STORY_GATE: VisualKind.TINY_DOOR,
    CompanionObjectType.DRAWING_CHARACTER: VisualKind.DINO_SHADOW,
    CompanionObjectType.BLOCK_MONSTER: VisualKind.BLOCK_LIGHT,
    CompanionObjectType.WINDOW_BIRD: VisualKind.CLOUD,
    CompanionObjectType.TOY_CHARACTER: VisualKind.BLOCK_LIGHT,
    CompanionObjectType.OTHER: VisualKind.STAR,
}


def resolve_visual_kind(object_type: str, source_type: str | None = None) -> str:
    """从 object_type 推导 visual_kind。未知类型兜底 star。"""
    try:
        ot = CompanionObjectType(object_type)
    except ValueError:
        return VisualKind.STAR
    return str(_OBJECT_TYPE_TO_VISUAL_KIND.get(ot, VisualKind.STAR))


class CompanionObjectCreateRequest(BaseModel):
    child_id: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=NAME_MAX_LENGTH)
    object_type: CompanionObjectType
    source_type: CompanionObjectSource
    safe_summary: str = Field(..., min_length=1, max_length=SAFE_SUMMARY_MAX_LENGTH)
    light_location: str = Field(..., min_length=1, max_length=40)


class CompanionObjectUpdateRequest(BaseModel):
    safe_summary: str | None = Field(
        default=None, min_length=1, max_length=SAFE_SUMMARY_MAX_LENGTH
    )
    light_location: str | None = Field(default=None, min_length=1, max_length=40)


class CompanionObject(BaseModel):
    id: str
    child_id: str
    name: str
    object_type: CompanionObjectType
    source_type: CompanionObjectSource
    safe_summary: str
    light_location: str
    status: CompanionObjectStatus
    visual_kind: str = VisualKind.STAR
    last_recalled_at: datetime | None
    recall_count: int
    skip_count: int
    created_at: datetime
    updated_at: datetime
