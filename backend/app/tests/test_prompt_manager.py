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
        PromptLayer.PARENT_POLICY,
        PromptLayer.SCENE,
        PromptLayer.MEMORY_CONTEXT,
        PromptLayer.OUTPUT_CONTRACT,
    ]
    assert "当前场景：放学后交流" in prompt.prompt
    assert "父亲规则" in prompt.prompt
    assert "近期对积木和太空主题感兴趣" in prompt.prompt
    assert prompt.prompt_versions["global_system"].version == "v0.1"
    assert (
        prompt.prompt_versions["scene"].filename
        == "scenes/daily_after_school_checkin_v0_1.txt"
    )
    assert prompt.prompt_versions["parent_policy"].version == "runtime:v2"


def test_learning_scene_prompt_requires_scaffolding_not_direct_answers() -> None:
    prompt = PromptManager().compose("learning.homework_help")

    assert "当前场景：学习求助" in prompt.prompt
    assert "不直接给最终答案" in prompt.prompt
    assert "不要直接给完整答案" in prompt.prompt
    assert "先引导审题和思路，不直接给最终答案" in prompt.prompt


def test_global_prompt_contains_no_secret_safety_rule() -> None:
    prompt = PromptManager().compose("daily.after_school_checkin")

    assert "不能要求孩子保密或保守秘密" in prompt.prompt
    assert "不能鼓励孩子隐瞒父母" in prompt.prompt


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
