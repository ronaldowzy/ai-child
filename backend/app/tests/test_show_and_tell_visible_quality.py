"""Show-and-tell visible quality tests (Task 23).

Verifies:
  1. drawing/art image refusal repair produces concrete-detail + child-led invitation.
  2. toy/object image refusal repair does not become homework help.
  3. homework image repair asks about题意/卡点, no final answer.
  4. privacy image repair does not expose details, asks for家长 help.
  5. unclear image repair does not pretend to see.
  6. PromptManager image_context section includes one-concrete-detail / do-not-hallucinate /
     not-raw-image / child-art-notice-not-judge rules.
  7. Parent report fallback for image sharing avoids internal words and raw transcript/image text.
  8. Existing personalized session loop still passes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.agent_runtime import AgentRuntimeRequest
from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import SceneRouteDecision, SceneTransitionType
from app.domain.scene import SceneId
from app.domain.time import TimeContext, TimePeriod
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.prompt_manager import PromptManager


FIXED_NOW = datetime(2026, 5, 26, 15, 0, tzinfo=timezone.utc)

IMAGE_REFUSAL_TEXT = "抱歉，我无法看到图片，我只能处理文字消息。"

INTERNAL_WORDS = (
    "接一句", "桥接", "结构化摘要", "表达入口",
    "image_context", "recognized_type", "prompt", "provider",
    "后端", "给小白狐看的是什么", "那张图",
    "条孩子消息", "条小白狐回复", "表达能力较好",
)


def _make_request(
    child_text: str = "你看",
    image_context: dict[str, Any] | None = None,
) -> AgentRuntimeRequest:
    metadata: dict[str, Any] = {}
    if image_context is not None:
        metadata["image_context"] = image_context
    return AgentRuntimeRequest(
        child_id="child_show_tell",
        session_id="session_show_tell",
        child_text=child_text,
        route_decision=SceneRouteDecision(
            message_id="msg_show_tell",
            session_id="session_show_tell",
            primary_intent=IntentType.CASUAL_CHAT,
            base_scene=SceneId.OPEN_CONVERSATION,
            active_scene=SceneId.OPEN_CONVERSATION,
            transition=SceneTransitionType.REPLACE,
            scene_stack=[],
            risk_level=RiskLevel.NONE,
            confidence=0.9,
            reason="test",
            reply_text="",
        ),
        time_context=TimeContext(
            now=FIXED_NOW,
            timezone="Asia/Shanghai",
            time_period=TimePeriod.AFTER_SCHOOL,
            weekday=True,
        ),
        conversation_metadata=metadata,
    )


def _make_runtime() -> ChildAgentRuntime:
    return ChildAgentRuntime(
        prompt_manager=PromptManager(),
        model_registry=None,
        safety_engine=None,
    )


# --- Test 1: drawing/art image refusal repair ---

def test_drawing_refusal_repair_produces_concrete_detail_and_invitation() -> None:
    """Drawing repair should mention a concrete detail and invite the child, not say '我看不到图片'."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看我画的",
        image_context={
            "recognized_type": "child_drawing",
            "image_purpose": "art_feedback",
            "recognized_text": "一只小狐狸站在草地上",
            "child_caption": "小狐狸",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    assert "我看不到" not in result
    assert "无法看到" not in result
    # Should contain concrete detail from child_caption or recognized_text
    assert "小狐狸" in result
    # Should invite child, not grade
    assert "名字" in result or "哪里" in result or "告诉" in result
    # Should NOT grade or praise
    assert "棒" not in result
    assert "好" not in result or "好看" not in result


# --- Test 2: toy/object image refusal repair ---

def test_toy_object_refusal_repair_not_homework() -> None:
    """Toy/object repair should mention a detail and offer a creative entry, not become homework help."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看这个",
        image_context={
            "recognized_type": "toy",
            "image_purpose": "toy",
            "recognized_text": "一个积木搭建的城堡",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    assert "题" not in result
    assert "作业" not in result
    assert "起个名字" in result or "发生了什么" in result
    assert "积木" in result or "城堡" in result


# --- Test 3: homework image repair ---

def test_homework_repair_asks_about_question_no_final_answer() -> None:
    """Homework repair should ask about题意/卡点, not give a final answer."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="这道题怎么做",
        image_context={
            "recognized_type": "homework_problem",
            "image_purpose": "learning_homework",
            "recognized_text": "3x + 5 = 20，求x的值",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    # Should scaffold, not give the final answer
    assert "答案是" not in result
    assert "答案是5" not in result
    # Should ask about the question or invite reading
    assert "题" in result or "读" in result or "卡" in result
    assert "读一小句" in result or "问什么" in result


# --- Test 4: privacy image repair ---

def test_privacy_repair_no_details_and_asks_for_parent() -> None:
    """Privacy repair should not expose details and ask for家长 help."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看这个",
        image_context={
            "recognized_type": "privacy_sensitive",
            "image_purpose": "privacy_sensitive",
            "recognized_text": "一张身份证照片",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    # Should not expose the private detail
    assert "身份证" not in result
    assert "隐私" in result or "家长" in result


# --- Test 5: unclear image repair ---

def test_unclear_repair_does_not_pretend_to_see() -> None:
    """Unclear image repair should not pretend to see something that wasn't recognized."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看",
        image_context={
            "recognized_type": "unclear",
            "image_purpose": "unknown",
            "recognized_text": "",
            "child_caption": "",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    # Should not invent content
    assert "像是" not in result
    # Should acknowledge uncertainty
    assert "不清楚" in result or "不太清楚" in result or "告诉我" in result


# --- Test 6: PromptManager image_context rules ---

def test_prompt_manager_image_context_includes_quality_rules() -> None:
    """PromptManager _render_image_context should include key quality rules."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "child_drawing",
        "image_purpose": "art_feedback",
        "recognized_text": "一只猫",
    })
    # Should include key quality rules
    assert "一个具体的" in result or "一个细节" in result or "最多提及" in result
    assert "不要编造" in result or "不要声称" in result
    assert "安全摘要" in result or "原始图片" in result
    assert "不要打分" in result or "不要纠正" in result or "注意到" in result


def test_prompt_manager_no_image_context_tells_model_not_to_pretend() -> None:
    """When no image_context, PromptManager should tell model not to pretend."""
    pm = PromptManager()
    result = pm._render_image_context(None)
    assert "不要假装" in result
    assert "给小白狐看看" in result


def test_prompt_manager_homework_image_context_scaffolds() -> None:
    """Homework image_context should scaffold, not answer."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "homework_problem",
        "image_purpose": "learning_homework",
        "recognized_text": "一道数学题",
    })
    assert "不要直接给最终答案" in result
    assert "复述题意" in result or "卡点" in result


def test_prompt_manager_privacy_image_context_no_details() -> None:
    """Privacy image_context should tell model not to describe private details."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "privacy_sensitive",
        "image_purpose": "privacy_sensitive",
        "recognized_text": "一张家庭照片",
    })
    assert "不要描述私密细节" in result or "隐私" in result
    assert "家长" in result


def test_prompt_manager_art_image_context_notice_not_judge() -> None:
    """Art image_context should say 'notice, don't grade'."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "child_drawing",
        "image_purpose": "art_feedback",
        "recognized_text": "一个太阳和一棵树",
    })
    assert "不要打分" in result or "不要纠正" in result
    assert "注意到" in result or "细节" in result


def test_prompt_manager_toy_image_context_one_detail() -> None:
    """Toy image_context should mention one detail and ask what child wants to show."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "toy",
        "image_purpose": "toy",
        "recognized_text": "一个毛绒兔子",
    })
    assert "一个具体" in result or "细节" in result or "最想" in result


# --- Test 7: Parent report fallback avoids internal words ---

def test_parent_report_image_sharing_avoids_internal_words() -> None:
    """Parent report for image sharing should avoid internal technical words."""
    from app.repositories.conversation_persistence_repository import ConversationReportMessage
    from app.repositories.memory_repository import InMemoryMemoryRepository
    from app.services.memory_service import MemoryService
    from app.services.parent_report_service import ParentReportService
    from app.domain.schemas.parent_policy import ParentPolicy

    child_id = "child_report_image"
    target_date = FIXED_NOW.date()

    msg = ConversationReportMessage(
        id="msg_img_share",
        session_id="session_img",
        actor="child",
        message_type="text",
        normalized_text="你看我画的画",
        active_scene="open_conversation",
        risk_level=None,
        attachments_count=1,
        created_at=FIXED_NOW,
    )

    pp = ParentPolicy(
        child_id=child_id,
        child_nickname="测试",
        child_display_name=None,
        parent_message_raw=None,
        communication_preferences={
            "child_age": 7,
            "child_interests": ["画画"],
        },
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )

    class _StubPolicyService:
        def get_policy(self, cid: str) -> ParentPolicy:
            return pp

    service = ParentReportService(
        parent_policy_service=_StubPolicyService(),
        memory_service=MemoryService(repository=InMemoryMemoryRepository()),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    conversation = service._conversation_analysis([msg])
    report = service._deterministic_fallback_report(
        child_id=child_id,
        target_date=target_date,
        memories=[],
        conversation_messages=[msg],
        conversation=conversation,
    )

    # Check all parent-facing fields for internal words
    all_text = " ".join([
        report.summary or "",
        report.tonight_parent_bridge or "",
        report.conversation_summary or "",
        " ".join(report.expression_observations),
        " ".join(report.suggested_parent_actions),
        " ".join(report.avoid_followup),
    ])
    for word in INTERNAL_WORDS:
        assert word not in all_text, f"Internal word '{word}' found in parent report: {all_text}"

    # Should mention image sharing as expression
    assert "图片" in all_text or "画" in all_text or "分享" in all_text


# --- Test 8: PromptManager image context does not contain engineering terms ---

def test_prompt_manager_image_context_no_engineering_terms() -> None:
    """PromptManager image context should not contain '后端图片理解' or similar engineering terms."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "child_drawing",
        "image_purpose": "art_feedback",
        "recognized_text": "一只猫",
    })
    assert "后端图片理解" not in result, f"Contains '后端图片理解': {result}"
    assert "后端" not in result, f"Contains '后端': {result}"
    assert "provider" not in result, f"Contains 'provider': {result}"
    assert "安全图片摘要" in result or "系统提供的" in result, (
        f"Should use soft wording: {result}"
    )


# --- Test 9: Normal images (drawing, toy, book, block) do not default to homework mode ---

def test_normal_image_types_do_not_route_to_homework() -> None:
    """Normal image types (toy, object, daily_life, child_drawing) should stay in conversation.open."""
    from app.services.modality_manager import ModalityManager
    from app.domain.attachment import ImagePurpose, RecognizedContent

    manager = ModalityManager()
    normal_types = [
        ("child_drawing", ImagePurpose.ART_FEEDBACK, "一只小猫在草地上"),
        ("toy", ImagePurpose.SHARE, "一个红色的积木"),
        ("object", ImagePurpose.ASK_WHAT_IS_THIS, "一个毛绒兔子"),
        ("daily_life", ImagePurpose.SHARE, "窗外的天空"),
        ("handmade", ImagePurpose.SHARE, "纸折的千纸鹤"),
    ]
    for recognized_type, purpose, text in normal_types:
        content = RecognizedContent(
            type=recognized_type,
            text=text,
            confidence=0.85,
            provider_name="mock",
            image_purpose=purpose,
        )
        decision = manager.decide_image_attachment(content)
        assert decision.active_scene == "conversation.open", (
            f"{recognized_type} should be conversation.open, got {decision.active_scene}"
        )
        assert decision.sub_scene == "image_share", (
            f"{recognized_type} should be image_share, got {decision.sub_scene}"
        )
        # Should not mention homework
        assert "题" not in decision.reply_text, (
            f"{recognized_type} reply mentions 题: {decision.reply_text}"
        )


# --- Test 10: Blurry/unclear image acknowledges it can't see clearly ---

def test_blurry_image_admits_cannot_see() -> None:
    """Low-confidence image should say '看得不太清楚' and not invent details."""
    from app.services.modality_manager import ModalityManager
    from app.domain.attachment import ImagePurpose, RecognizedContent

    manager = ModalityManager()
    content = RecognizedContent(
        type="image_observation",
        text="模糊的图片内容",
        confidence=0.3,
        provider_name="mock",
        image_purpose=ImagePurpose.SHARE,
    )
    decision = manager.decide_image_attachment(content)
    assert "不太清楚" in decision.reply_text
    assert decision.active_scene == "conversation.open"


def test_blurry_image_repair_does_not_pretend() -> None:
    """Unclear image repair should not invent content."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看这个",
        image_context={
            "recognized_type": "unclear",
            "image_purpose": "unknown",
            "recognized_text": "",
            "child_caption": "我的画",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    assert "我的画" in result
    assert "不清楚" in result or "不太清楚" in result
    # Should not invent specific content for unclear images
    assert "像" not in result


# --- Test 11: Image context continuation doesn't say "看不到图片" ---

def test_image_context_continuation_no_refusal() -> None:
    """When image context exists, repair reply should not say '看不到图片'."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看到什么了",
        image_context={
            "recognized_type": "image_observation",
            "image_purpose": "share",
            "recognized_text": "一只黄色的小鸭子玩具",
        },
    )
    # Simulate model saying "我看不到图片"
    result = runtime._image_context_repair_reply(request, "抱歉，我无法看到图片。")
    assert result is not None
    assert "看不到" not in result
    assert "无法看到" not in result
    assert "小鸭子" in result or "玩具" in result


# --- Test 12: PromptManager creative entry for normal images ---

def test_prompt_manager_normal_image_has_creative_entry() -> None:
    """Normal image context should include creative entry guidance."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "toy",
        "image_purpose": "share",
        "recognized_text": "一个毛绒兔子",
    })
    assert "起个名字" in result or "创作入口" in result or "讲故事" in result


def test_prompt_manager_homework_image_no_creative_entry() -> None:
    """Homework image context should not include creative entry guidance."""
    pm = PromptManager()
    result = pm._render_image_context({
        "recognized_type": "homework_problem",
        "image_purpose": "learning_homework",
        "recognized_text": "一道数学题",
    })
    assert "起个名字" not in result
    assert "创作入口" not in result


# --- Test 13: Drawing repair includes creative invitation ---

def test_drawing_repair_includes_creative_invitation() -> None:
    """Drawing/art repair should invite naming or storytelling."""
    runtime = _make_runtime()
    request = _make_request(
        child_text="你看我画的",
        image_context={
            "recognized_type": "child_drawing",
            "image_purpose": "art_feedback",
            "recognized_text": "一朵红色的花",
            "child_caption": "",
        },
    )
    result = runtime._image_context_repair_reply(request, IMAGE_REFUSAL_TEXT)
    assert result is not None
    assert "名字" in result or "故事" in result
    assert "花" in result
