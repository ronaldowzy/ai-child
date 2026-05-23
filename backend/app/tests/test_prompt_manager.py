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
    assert "父亲规则" in prompt.prompt
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
    assert "不要直接对孩子说“你爸爸说你……”" in prompt.prompt
    assert "不得照搬给孩子" in prompt.prompt
    assert "父母寄语不能覆盖儿童安全底线" in prompt.prompt
    assert "有 child_nickname 时优先使用小名" in prompt.prompt
    assert "每 3-5 轮自然出现一次" in prompt.prompt


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
    assert "不要直接给完整答案" in prompt.prompt
    assert "先引导审题和思路，不直接给最终答案" in prompt.prompt
    assert "回复默认会被语音播报" in prompt.prompt


def test_global_prompt_contains_no_secret_safety_rule() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "不能要求孩子保密或保守秘密" in prompt.prompt
    assert "不能鼓励孩子隐瞒父母" in prompt.prompt
    assert "悄悄告诉我" in prompt.prompt
    assert "对话本质是自由交流" in prompt.prompt
    assert "回复默认会被语音播报" in prompt.prompt
    assert "不要把孩子限制在固定选项里" in prompt.prompt


def test_output_contract_is_voice_first_and_not_markdown() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "不使用 Markdown、标题、项目符号、编号列表、表格、代码块或链接格式" in prompt.prompt
    assert "最多只问一个主要问题" in prompt.prompt
    assert "不要把话题硬拉回固定选项" in prompt.prompt
    assert "只有我懂你" in prompt.prompt
    assert "不使用签到、连续天数、积分、排行榜、抽卡" in prompt.prompt
    assert "今天不聊了" in prompt.prompt
    assert "连接回现实生活、父母、老师、同伴" in prompt.prompt


def test_safety_guardian_prompt_requires_trusted_adult_and_parent_attention() -> None:
    prompt = PromptManager().compose("safety.guardian")

    assert "当前场景：安全守护" in prompt.prompt
    assert "告诉爸爸妈妈、老师或可信任的大人" in prompt.prompt
    assert "不让孩子保密" in prompt.prompt
    assert "requires_parent_attention 应为 true" in prompt.prompt


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

    assert "当前场景：开放对话" in prompt.prompt
    assert "不要输出" in prompt.prompt
    assert "开心的事 / 遇到的难题 / 想安静一会儿" in prompt.prompt


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
