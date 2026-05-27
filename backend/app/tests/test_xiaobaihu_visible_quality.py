from pathlib import Path

from app.domain.attachment import AttachmentStatus, ImagePurpose, RecognizedContent
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.modality_manager import ModalityManager
from app.services.opening_policy import FORBIDDEN_OPENING_PHRASES
from app.services.parent_report_service import ParentReportService
from app.services.prompt_manager import PromptManager
from app.services.safety_engine import SafetyEngine


PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts"
REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs"


DEPENDENCY_MARKERS = (
    "唯一的朋友",
    "最懂你",
    "小白狐会想你",
    "我一直等你",
    "你不来我会难过",
)
RETENTION_MARKERS = (
    "连续签到",
    "不要断签",
    "积分",
    "排行榜",
    "抽卡",
    "限时奖励",
    "错过就没有",
    "宠物饥饿",
)
INTERNAL_CHILD_MARKERS = (
    "backend",
    "provider",
    "ASR",
    "TTS",
    "prompt",
    "debug",
    "error code",
)


def _all_prompt_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in PROMPT_ROOT.rglob("*.txt")
    )


def _assert_child_visible_clean(text: str) -> None:
    assert not any(marker in text for marker in INTERNAL_CHILD_MARKERS)
    assert not any(marker in text for marker in DEPENDENCY_MARKERS)
    assert not any(marker in text for marker in RETENTION_MARKERS)


def test_xiaobaihu_style_guide_exists_and_sets_friend_companion_direction() -> None:
    guide = (DOCS_ROOT / "小白狐提示语与文案规范_V0_1.md").read_text(
        encoding="utf-8"
    )

    assert "愿意听孩子分享" in guide
    assert "不是孩子唯一的朋友" in guide
    assert "不替代家长、老师、同伴或现实生活" in guide
    assert "拍给小白狐看" in guide
    assert "家长端语言" in guide


def test_prompt_templates_contain_core_guardrails() -> None:
    prompt_text = _all_prompt_text()

    assert "不直接输出最终答案" in prompt_text
    assert "不要要求孩子隐瞒家长、老师或其他可信成人" in prompt_text
    assert "家长、老师或身边安全的大人" in prompt_text
    assert "不把所有图片都当作作业" in prompt_text
    assert "不把睡前变成复盘作业、成长打卡或挑战任务" in prompt_text


def test_learning_prompt_scaffolds_and_does_not_allow_final_answer() -> None:
    prompt = PromptManager().compose("learning.homework_help").prompt

    assert "当前场景：学习求助" in prompt
    assert "不直接替孩子完成作业" in prompt
    assert "每次只推进一个很小的思考步骤" in prompt
    assert "你太粗心" not in prompt
    assert "你不聪明" not in prompt


def test_safety_and_privacy_prompts_encourage_trusted_adult_without_collecting_more() -> None:
    safety_prompt = PromptManager().compose("safety.guardian").prompt
    privacy_prompt = PromptManager().compose("privacy.boundary").prompt

    assert "告诉家长、老师或可信任的大人" in safety_prompt
    assert "不询问具体隐私细节" in safety_prompt
    assert "不索要真实地址、电话、学校、照片或身份信息" in privacy_prompt
    assert "不要求孩子保密" in privacy_prompt


def test_image_context_prompt_does_not_default_to_homework_or_refuse_seen_image() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        image_context={
            "attachment_id": "att_share",
            "image_purpose": "share",
            "recognized_type": "image_observation",
            "recognized_text": "孩子搭了一个积木城堡",
            "child_caption": "你看这个",
        },
    ).prompt

    assert "不要说你看不到图片、不能看图片或没有看图功能" in prompt
    assert "不要把它强行当成作业" in prompt
    assert "最多提及一个具体、安全、被摘要支持的细节" in prompt


def test_modality_image_share_copy_is_child_visible_and_not_homework_first() -> None:
    decision = ModalityManager().decide_image_attachment(
        RecognizedContent(
            type="image_observation",
            text="孩子搭了一个积木城堡",
            confidence=0.9,
            provider_name="test_vision",
            image_purpose=ImagePurpose.SHARE,
        )
    )

    assert decision.status == AttachmentStatus.IMAGE_READY
    assert decision.active_scene == "conversation.open"
    assert "题" not in decision.reply_text
    assert "作业" not in decision.reply_text
    _assert_child_visible_clean(decision.reply_text)


def test_bedtime_prompt_is_low_stimulation_and_not_retention_hook() -> None:
    prompt = PromptManager().compose("daily.bedtime_reflection").prompt

    assert "低刺激" in prompt
    assert "我们慢慢收个尾" in prompt
    assert "不把睡前变成复盘作业、成长打卡或挑战任务" in prompt
    assert "明天一定回来" in prompt  # only appears as forbidden guidance.
    assert "小白狐会想你" in prompt  # only appears as forbidden guidance.


def test_opening_forbidden_phrases_block_dependency_and_retention_language() -> None:
    forbidden = "\n".join(FORBIDDEN_OPENING_PHRASES)

    assert "只有小白狐懂你" in forbidden
    assert "这是我们的小秘密" in forbidden
    assert "我一直等你" in forbidden
    assert "连续来几天就有惊喜" in forbidden
    assert "每天都要来" in forbidden


def test_runtime_child_fallbacks_do_not_expose_internal_terms() -> None:
    runtime = ChildAgentRuntime()
    fallback_texts = [
        runtime.SELF_HARM_GUARDIAN_REPLY,
        runtime.BEDTIME_CLOSE_REPLY,
        runtime._topic_shift_reply(type("Ctx", (), {"suggested_topic_seeds": []})()),
    ]

    for text in fallback_texts:
        _assert_child_visible_clean(text)


def test_parent_report_prompt_is_not_monitoring_or_usage_stats() -> None:
    prompt = ParentReportService()._parent_report_system_prompt()

    assert "不要把日报写成聊天监控、使用统计、老师评语、心理诊断、行为评分或家长盘问清单" in prompt
    assert "不要暴露孩子和小白狐逐句聊了什么" in prompt
    assert "不要输出逐字聊天记录" in prompt
    assert "不要要求孩子复述和小白狐的聊天内容" in prompt


def test_safety_engine_blocks_dependency_secret_and_retention_outputs() -> None:
    engine = SafetyEngine()

    assert engine.classify_output("这是我们的小秘密。只告诉我。").requires_parent_attention
    assert engine.classify_output("我是你唯一的朋友。只有我懂你。").requires_parent_attention
    assert engine.classify_output("每天都要来看我，连续签到有奖励。").requires_parent_attention
