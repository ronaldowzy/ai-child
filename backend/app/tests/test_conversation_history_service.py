from app.services.conversation_history_service import ConversationHistoryService


def test_conversation_history_records_recent_turns_for_model_context() -> None:
    service = ConversationHistoryService(max_messages_per_session=4)

    service.record_turn(
        session_id="history_session",
        child_text="我想聊恐龙",
        agent_text="你喜欢哪种恐龙？",
    )
    service.record_turn(
        session_id="history_session",
        child_text="三角龙",
        agent_text="三角龙的角很特别。",
    )
    service.record_turn(
        session_id="history_session",
        child_text="它吃什么",
        agent_text="它主要吃植物。",
    )

    messages = service.get_recent_model_messages(session_id="history_session", limit=4)

    assert [message.role for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert messages[0].content == "三角龙"
    assert messages[-1].content == "它主要吃植物。"


def test_conversation_history_does_not_mix_sessions() -> None:
    service = ConversationHistoryService()

    service.record_turn(
        session_id="session_a",
        child_text="我想聊恐龙",
        agent_text="可以。",
    )
    service.record_turn(
        session_id="session_b",
        child_text="我想聊火山",
        agent_text="可以聊火山。",
    )

    messages = service.get_recent_model_messages(session_id="session_a", limit=6)

    assert [message.content for message in messages] == ["我想聊恐龙", "可以。"]
