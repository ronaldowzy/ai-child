from pydantic import BaseModel, Field

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)


class MemoryExtractionRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    chat_summary: str = Field(..., min_length=1, max_length=1000)
    safety_requires_parent_attention: bool = False


class MemoryExtractionResult(BaseModel):
    memories: list[MemoryCreateRequest] = Field(default_factory=list)
    write_allowed: bool = True
    retention: str = "structured_only"


class MemoryExtractor:
    """Rule-based mock extractor that emits structured memories only."""

    def extract(self, request: MemoryExtractionRequest) -> MemoryExtractionResult:
        summary = request.chat_summary.strip()
        normalized = summary.replace(" ", "")
        memories: list[MemoryCreateRequest] = []

        if self._contains_any(normalized, ("恐龙", "霸王龙", "三角龙")):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.INTEREST,
                    content="孩子对恐龙话题表现出兴趣，可作为之后表达和阅读的切入点。",
                    tags=["恐龙", "兴趣", "表达切入点"],
                    confidence=0.78,
                    importance=0.6,
                )
            )

        if self._contains_any(normalized, ("数学", "题", "作业", "不会")):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.LEARNING_PATTERN,
                    content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
                    tags=["学习求助", "题意确认", "分步引导"],
                    confidence=0.74,
                    importance=0.75,
                    sensitivity=MemorySensitivity.MEDIUM,
                )
            )

        if self._contains_any(normalized, ("不想说话", "选择题", "选一个")):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.EXPRESSION_PATTERN,
                    content="孩子在开放提问下回答较短，使用选择题式引导时更容易开始表达。",
                    tags=["表达", "选择题有效", "低压力提问"],
                    confidence=0.7,
                    importance=0.7,
                    sensitivity=MemorySensitivity.MEDIUM,
                )
            )

        if self._contains_any(normalized, ("难过", "害怕", "生气", "很烦", "好累")):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.EMOTION_OBSERVATION,
                    content="孩子本次表达了低落或紧张情绪，后续适合先接住感受再进入问题解决。",
                    tags=["情绪观察", "先共情", "短期关注"],
                    confidence=0.72,
                    importance=0.8,
                    sensitivity=MemorySensitivity.MEDIUM,
                )
            )

        if self._contains_any(normalized, ("先复述", "一步一步", "换个说法")):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.STRATEGY,
                    content="先请孩子复述题意或换个说法，再继续追问下一步，可能更适合本阶段学习支持。",
                    tags=["引导策略", "复述题意", "分步"],
                    confidence=0.68,
                    importance=0.7,
                )
            )

        if request.safety_requires_parent_attention or self._contains_any(
            normalized,
            ("陌生人", "网友", "不要告诉爸爸", "不要告诉妈妈", "保密", "自杀", "想死"),
        ):
            memories.append(
                self._build_memory(
                    request=request,
                    memory_type=MemoryType.SAFETY,
                    content="本次会话出现需要家长关注的安全信号，应由家长进一步了解情况。",
                    tags=["安全提醒", "家长关注"],
                    confidence=0.9,
                    importance=1.0,
                    sensitivity=MemorySensitivity.CRITICAL,
                    requires_parent_attention=True,
                )
            )

        return MemoryExtractionResult(memories=memories)

    def _build_memory(
        self,
        *,
        request: MemoryExtractionRequest,
        memory_type: MemoryType,
        content: str,
        tags: list[str],
        confidence: float,
        importance: float,
        sensitivity: MemorySensitivity = MemorySensitivity.LOW,
        requires_parent_attention: bool = False,
    ) -> MemoryCreateRequest:
        return MemoryCreateRequest(
            child_id=request.child_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            evidence=[
                MemoryEvidence(
                    source="chat_summary",
                    session_id=request.session_id,
                    quote_summary=self._quote_summary(request.chat_summary),
                )
            ],
            confidence=confidence,
            importance=importance,
            sensitivity=sensitivity,
            visible_to_parent=True,
            visible_to_child=False,
            requires_parent_attention=requires_parent_attention,
        )

    def _quote_summary(self, chat_summary: str) -> str:
        summary = " ".join(chat_summary.strip().split())
        return summary[:160]

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)


_memory_extractor = MemoryExtractor()


def get_memory_extractor() -> MemoryExtractor:
    return _memory_extractor
