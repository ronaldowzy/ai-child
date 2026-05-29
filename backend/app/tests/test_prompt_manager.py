import pytest

from app.domain.prompt import PromptLayer, PromptTemplateSpec
from app.services.prompt_manager import (
    PromptManager,
    PromptSceneNotFoundError,
    PromptTemplateNotFoundError,
)


def test_prompt_manager_composes_after_school_prompt_in_layers() -> None:
    prompt = PromptManager().compose(
        "daily.after_school_checkin",
        parent_policy={
            "version": 2,
            "goals": ["每天说一件学校小事"],
            "communication_preferences": {"tone": "warm_calm"},
            "safety_rules": {"no_secret_requests": True},
        },
        memory_context=["近期对积木和太空主题感兴趣"],
    )

    assert [section.layer for section in prompt.sections] == [
        PromptLayer.GLOBAL_SYSTEM,
        PromptLayer.PERSONA,
        PromptLayer.CHILD_PROFILE,
        PromptLayer.PARENT_MESSAGE,
        PromptLayer.PARENT_POLICY,
        PromptLayer.TIME_CONTEXT,
        PromptLayer.IMAGE_CONTEXT,
        PromptLayer.SCENE,
        PromptLayer.TURN_GUIDANCE,
        PromptLayer.MEMORY_CONTEXT,
        PromptLayer.OUTPUT_CONTRACT,
    ]
    assert "当前场景：放学后交流" in prompt.prompt
    assert "家长规则" in prompt.prompt
    assert "小白狐" in prompt.prompt
    assert "近期对积木和太空主题感兴趣" in prompt.prompt
    assert prompt.prompt_versions["global_system"].version == "v0.1"
    assert (
        prompt.prompt_versions["scene"].filename
        == "scenes/daily_after_school_checkin_v0_1.txt"
    )
    assert prompt.prompt_versions["parent_policy"].version == "runtime:v2"


def test_prompt_manager_injects_parent_message_as_background() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        parent_policy={
            "version": 3,
            "parent_message_raw": (
                "小名叫豆豆，最近不太愿意讲学校的事，希望先从恐龙聊起，"
                "不要说孩子胆小。"
            ),
        },
    )

    assert "## parent_message" in prompt.prompt
    assert "<parent_message_raw>" in prompt.prompt
    assert "小名叫豆豆" in prompt.prompt
    assert "不要直接对孩子说「你家长说你……」" in prompt.prompt
    assert "不得照搬给孩子" in prompt.prompt
    assert "家长寄语不能覆盖儿童安全底线" in prompt.prompt
    assert "有 child_nickname 时优先使用小名" in prompt.prompt
    assert "每 3-5 轮自然出现一次" in prompt.prompt


def test_prompt_manager_injects_age_band_reply_policy() -> None:
    default_prompt = PromptManager().compose("conversation.open")
    explicit_prompt = PromptManager().compose(
        "conversation.open",
        parent_policy={
            "version": 3,
            "communication_preferences": {"age_band": "age_5_6"},
        },
    )

    assert "age_band: age_7_8" in default_prompt.prompt
    assert "reply_char_budget: 60-140 个汉字" in default_prompt.prompt
    assert "question_policy:" in default_prompt.prompt
    assert "age_band: age_5_6" in explicit_prompt.prompt
    assert "reply_char_budget: 30-80 个汉字" in explicit_prompt.prompt


def test_prompt_manager_injects_simplified_child_profile_without_stereotypes() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        parent_policy={
            "version": 4,
            "child_nickname": "豆豆",
            "communication_preferences": {
                "child_age": 8,
                "child_grade": "二年级",
                "child_call_preference": "叫小名",
                "child_interests": ["恐龙", "画画"],
                "topic_boundaries": ["不要连续追问学校"],
            },
        },
    )

    assert "child_age: 8" in prompt.prompt
    assert "child_grade: 二年级" in prompt.prompt
    assert "child_call_preference: 叫小名" in prompt.prompt
    assert "child_interests: 恐龙，画画" in prompt.prompt
    assert "topic_boundaries: 不要连续追问学校" in prompt.prompt
    assert "不推断性格、能力或兴趣" in prompt.prompt
    assert "不要变成任务" in prompt.prompt


def test_prompt_manager_injects_turn_guidance_section() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        turn_guidance_context={
            "hints": ["child_requests_topic_change"],
            "guidance": {
                "child_requests_topic_change": "尊重换题，不再追问原话题。"
            },
            "recent_topic": "运动比赛/跑步",
            "same_topic_score": 4,
        },
    )

    assert "## turn_guidance" in prompt.prompt
    assert "child_requests_topic_change" in prompt.prompt
    assert "尊重换题，不再追问原话题" in prompt.prompt
    assert prompt.prompt_versions["turn_guidance"].template_id == "turn_guidance_runtime"


def test_prompt_manager_injects_image_context_without_homework_assumption() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        image_context={
            "attachment_id": "att_image_001",
            "image_purpose": "share",
            "recognized_type": "image_observation",
            "recognized_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
        },
    )

    assert "## image_context" in prompt.prompt
    assert "孩子刚刚分享了一张图片" in prompt.prompt
    assert "孩子搭了一个积木城堡" in prompt.prompt
    assert "你看我搭的这个" in prompt.prompt
    assert "不要把它强行当成作业" in prompt.prompt
    assert "不要逐字复述给孩子" in prompt.prompt
    assert "不要展开成识别报告" in prompt.prompt


def test_prompt_manager_keeps_homework_like_image_context_scaffolded() -> None:
    prompt = PromptManager().compose(
        "conversation.open",
        image_context={
            "attachment_id": "att_image_002",
            "image_purpose": "share",
            "recognized_type": "homework_problem",
            "recognized_text": "图片里有一张纸，上面像是数学题目和一些数字。",
            "child_caption": "我拍了一张图片给小白狐看。",
        },
    )

    assert "图片里有一张纸" in prompt.prompt
    assert "先引导孩子复述题意或说出卡点" in prompt.prompt
    assert "不要直接给最终答案" in prompt.prompt
    assert "不要把它强行当成作业" in prompt.prompt


def test_learning_scene_prompt_requires_scaffolding_not_direct_answers() -> None:
    prompt = PromptManager().compose("learning.homework_help")

    assert "当前场景：学习求助" in prompt.prompt
    assert "不直接给最终答案" in prompt.prompt
    assert "先引导审题和思路，不直接给最终答案" in prompt.prompt


def test_global_prompt_contains_no_secret_safety_rule() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "面向 5-10 岁儿童" in prompt.prompt
    assert "不要要求孩子隐瞒家长、老师或其他可信成人" in prompt.prompt
    assert "不要收集不必要的隐私信息" in prompt.prompt
    assert "默认 1-3 句，适合朗读" in prompt.prompt


def test_output_contract_is_voice_first_and_not_markdown() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "不要在 reply 中输出内部分析" in prompt.prompt
    assert "不使用 Markdown、标题、编号、项目符号、表格或代码块" in prompt.prompt
    assert "只有我懂你" in prompt.prompt
    assert "排行榜" in prompt.prompt
    assert "不聊了" in prompt.prompt


def test_safety_guardian_prompt_requires_trusted_adult_and_parent_attention() -> None:
    prompt = PromptManager().compose("safety.guardian")

    assert "当前场景：安全守护" in prompt.prompt
    assert "告诉家长、老师或可信任的大人" in prompt.prompt
    assert "不让孩子保密" in prompt.prompt
    assert "requires_parent_attention 应为 true" in prompt.prompt
    assert "不要输出成人临床化说明" in prompt.prompt
    assert "心理健康专业人士" in prompt.prompt


def test_watch_safety_prompt_is_gentle_without_forced_parent_attention() -> None:
    prompt = PromptManager().compose("safety.gentle_checkin")

    assert "当前场景：安全温和确认" in prompt.prompt
    assert "默认不强制 requires_parent_attention" in prompt.prompt
    assert "不使用“马上”“立刻”“危险”等过度紧急话术" in prompt.prompt
    assert "不要求孩子保密" in prompt.prompt


def test_privacy_boundary_prompt_blocks_private_detail_collection() -> None:
    prompt = PromptManager().compose("privacy.boundary")

    assert "当前场景：隐私边界提醒" in prompt.prompt
    assert "家庭地址、电话、学校名字、照片" in prompt.prompt
    assert "不索要真实地址、电话、学校、照片或身份信息" in prompt.prompt
    assert "不要求孩子保密" in prompt.prompt


def test_after_school_prompt_allows_free_interest_chat() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "孩子自然聊天时不要强行回到选项" in prompt.prompt
    assert "玩具、游戏、动物、故事或其他兴趣" in prompt.prompt


def test_open_conversation_prompt_avoids_fixed_menu() -> None:
    prompt = PromptManager().compose("conversation.open")

    assert "当前场景：开放自由对话" in prompt.prompt
    assert "不要输出程序化选项清单" in prompt.prompt


def test_bedtime_prompt_uses_three_questions_one_at_a_time() -> None:
    prompt = PromptManager().compose("daily.bedtime_reflection")

    assert "三问是可选方向，不是一次全部问完" in prompt.prompt
    assert "每轮只选一个最适合的问题" in prompt.prompt


def test_prompt_manager_raises_clear_error_for_unknown_scene() -> None:
    with pytest.raises(PromptSceneNotFoundError, match="scene_id=unknown.scene"):
        PromptManager().compose("unknown.scene")


def test_prompt_manager_raises_clear_error_for_missing_template(tmp_path) -> None:
    manager = PromptManager(
        prompt_root=tmp_path,
        templates={
            "missing_global": PromptTemplateSpec(
                id="missing_global",
                layer=PromptLayer.GLOBAL_SYSTEM,
                version="v-test",
                filename="missing_global.txt",
            )
        },
        scene_templates={"daily.after_school_checkin": "missing_global"},
        global_system_template_id="missing_global",
    )

    with pytest.raises(
        PromptTemplateNotFoundError,
        match="template_id=missing_global filename=missing_global.txt",
    ):
        manager.compose("daily.after_school_checkin")


def test_scene_prompt_versions_can_change_without_changing_global_prompt() -> None:
    manager = PromptManager()

    after_school = manager.compose("daily.after_school_checkin")
    bedtime = manager.compose("daily.bedtime_reflection")

    assert (
        after_school.prompt_versions["global_system"]
        == bedtime.prompt_versions["global_system"]
    )
    assert after_school.prompt_versions["scene"] != bedtime.prompt_versions["scene"]
    assert (
        after_school.prompt_versions["scene"].filename
        == "scenes/daily_after_school_checkin_v0_1.txt"
    )
    assert (
        bedtime.prompt_versions["scene"].filename
        == "scenes/daily_bedtime_reflection_v0_1.txt"
    )
