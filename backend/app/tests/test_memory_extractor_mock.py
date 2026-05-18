from app.domain.memory import MemorySensitivity, MemoryType
from app.services.memory_extractor import MemoryExtractionRequest, MemoryExtractor


def test_memory_extractor_mock_outputs_structured_interest_and_learning_memories() -> None:
    extractor = MemoryExtractor()

    result = extractor.extract(
        MemoryExtractionRequest(
            child_id="child_memory_extractor_test",
            session_id="session_memory_extractor_test",
            chat_summary="孩子主动聊恐龙，也说有一道数学题不会，希望一步一步看题意。",
        )
    )

    memory_types = {memory.memory_type for memory in result.memories}

    assert result.write_allowed is True
    assert result.retention == "structured_only"
    assert MemoryType.INTEREST in memory_types
    assert MemoryType.LEARNING_PATTERN in memory_types
    assert MemoryType.STRATEGY in memory_types
    assert all(memory.evidence for memory in result.memories)
    assert all(memory.evidence[0].source == "chat_summary" for memory in result.memories)
    assert all(memory.confidence > 0 for memory in result.memories)


def test_memory_extractor_mock_marks_safety_memory_for_parent_attention() -> None:
    extractor = MemoryExtractor()

    result = extractor.extract(
        MemoryExtractionRequest(
            child_id="child_memory_extractor_safety_test",
            session_id="session_memory_extractor_safety_test",
            chat_summary="孩子提到有陌生人让他保密，不要告诉爸爸。",
            safety_requires_parent_attention=True,
        )
    )

    safety_memories = [
        memory
        for memory in result.memories
        if memory.memory_type == MemoryType.SAFETY
    ]

    assert len(safety_memories) == 1
    assert safety_memories[0].sensitivity == MemorySensitivity.CRITICAL
    assert safety_memories[0].requires_parent_attention is True
    assert safety_memories[0].visible_to_parent is True


def test_memory_extractor_mock_uses_observational_language() -> None:
    extractor = MemoryExtractor()

    result = extractor.extract(
        MemoryExtractionRequest(
            child_id="child_memory_extractor_expression_test",
            session_id="session_memory_extractor_expression_test",
            chat_summary="孩子不想说话时，选择题式提问帮助他选一个选项继续表达。",
        )
    )

    contents = " ".join(memory.content for memory in result.memories)

    assert MemoryType.EXPRESSION_PATTERN in {
        memory.memory_type for memory in result.memories
    }
    assert "孩子胆小" not in contents
    assert "孩子不合群" not in contents
    assert "内向是缺陷" not in contents
