from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from app.domain.prompt import (
    ComposedPrompt,
    PromptLayer,
    PromptSection,
    PromptTemplateSpec,
    PromptVersion,
)


class PromptManagerError(RuntimeError):
    pass


class PromptSceneNotFoundError(PromptManagerError):
    def __init__(self, scene_id: str) -> None:
        super().__init__(f"No scene prompt template configured for scene_id={scene_id}")
        self.scene_id = scene_id


class PromptTemplateNotFoundError(PromptManagerError):
    def __init__(self, template_id: str, filename: str, prompt_root: Path) -> None:
        super().__init__(
            "Missing prompt template "
            f"template_id={template_id} filename={filename} prompt_root={prompt_root}"
        )
        self.template_id = template_id
        self.filename = filename
        self.prompt_root = prompt_root


class PromptManager:
    def __init__(
        self,
        *,
        prompt_root: Path | None = None,
        templates: Mapping[str, PromptTemplateSpec] | None = None,
        scene_templates: Mapping[str, str] | None = None,
        global_system_template_id: str = "global_system_v0_1",
        persona_template_id: str = "persona_little_fox_v0_1",
        output_contract_template_id: str = "output_contract_child_chat_v0_1",
    ) -> None:
        self._prompt_root = (
            prompt_root or Path(__file__).resolve().parents[1] / "prompts"
        )
        self._templates = dict(
            templates if templates is not None else self._default_templates()
        )
        self._scene_templates = dict(
            scene_templates
            if scene_templates is not None
            else self._default_scene_templates()
        )
        self._global_system_template_id = global_system_template_id
        self._persona_template_id = persona_template_id
        self._output_contract_template_id = output_contract_template_id

    def compose(
        self,
        scene_id: str,
        *,
        parent_policy: Any | None = None,
        memory_context: Sequence[Any] | Mapping[str, Any] | str | None = None,
        persona_template_id: str | None = None,
        output_contract_template_id: str | None = None,
    ) -> ComposedPrompt:
        sections = [
            self._load_template_section(self._global_system_template_id),
            self._load_template_section(
                persona_template_id or self._persona_template_id
            ),
            self._build_parent_policy_section(parent_policy),
            self._load_scene_section(scene_id),
            self._build_memory_context_section(memory_context),
            self._load_template_section(
                output_contract_template_id or self._output_contract_template_id
            ),
        ]

        prompt = "\n\n".join(self._format_section(section) for section in sections)
        return ComposedPrompt(
            scene_id=scene_id,
            prompt=prompt,
            sections=sections,
            prompt_versions={
                section.layer.value: PromptVersion(
                    layer=section.layer,
                    template_id=section.template_id,
                    version=section.version,
                    filename=section.filename,
                )
                for section in sections
            },
        )

    def _load_scene_section(self, scene_id: str) -> PromptSection:
        template_id = self._scene_templates.get(scene_id)
        if template_id is None:
            raise PromptSceneNotFoundError(scene_id)
        return self._load_template_section(template_id)

    def _load_template_section(self, template_id: str) -> PromptSection:
        spec = self._templates.get(template_id)
        if spec is None:
            raise PromptTemplateNotFoundError(
                template_id,
                "<unregistered>",
                self._prompt_root,
            )

        template_path = self._prompt_root / spec.filename
        if not template_path.is_file():
            raise PromptTemplateNotFoundError(
                template_id,
                spec.filename,
                self._prompt_root,
            )

        content = template_path.read_text(encoding="utf-8").strip()
        return PromptSection(
            layer=spec.layer,
            template_id=spec.id,
            version=spec.version,
            filename=spec.filename,
            content=content,
        )

    def _build_parent_policy_section(self, parent_policy: Any | None) -> PromptSection:
        version = self._runtime_version(parent_policy)
        return PromptSection(
            layer=PromptLayer.PARENT_POLICY,
            template_id="parent_policy_runtime",
            version=version,
            filename=None,
            content=self._render_parent_policy(parent_policy),
        )

    def _build_memory_context_section(
        self,
        memory_context: Sequence[Any] | Mapping[str, Any] | str | None,
    ) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.MEMORY_CONTEXT,
            template_id="memory_context_runtime",
            version="runtime",
            filename=None,
            content=self._render_memory_context(memory_context),
        )

    def _render_parent_policy(self, parent_policy: Any | None) -> str:
        if parent_policy is None:
            return "父亲当前没有提供额外规则。继续遵守全局安全底线。"
        if isinstance(parent_policy, str):
            return parent_policy.strip()

        data = self._to_mapping(parent_policy)
        if not data:
            return "父亲当前没有提供额外规则。继续遵守全局安全底线。"

        lines = ["父亲规则："]
        goals = data.get("goals")
        if goals:
            lines.append(f"- 目标：{self._compact_value(goals)}")

        communication_preferences = data.get("communication_preferences")
        if communication_preferences:
            lines.append(
                "- 沟通偏好："
                f"{self._compact_value(communication_preferences)}"
            )

        safety_rules = data.get("safety_rules")
        if safety_rules:
            lines.append(f"- 安全规则：{self._compact_value(safety_rules)}")

        if len(lines) == 1:
            lines.append(f"- 规则摘要：{self._compact_value(data)}")
        return "\n".join(lines)

    def _render_memory_context(
        self,
        memory_context: Sequence[Any] | Mapping[str, Any] | str | None,
    ) -> str:
        if memory_context is None:
            return "当前没有可用的长期记忆。不要编造孩子的经历。"
        if isinstance(memory_context, str):
            text = memory_context.strip()
            return text or "当前没有可用的长期记忆。不要编造孩子的经历。"
        if isinstance(memory_context, Mapping):
            return f"可用记忆：\n- {self._compact_value(memory_context)}"

        items = [self._compact_value(item) for item in memory_context if item]
        if not items:
            return "当前没有可用的长期记忆。不要编造孩子的经历。"
        return "可用记忆：\n" + "\n".join(f"- {item}" for item in items)

    def _runtime_version(self, value: Any | None) -> str:
        if value is None or isinstance(value, str):
            return "runtime"
        data = self._to_mapping(value)
        version = data.get("version")
        if version is None:
            return "runtime"
        return f"runtime:v{version}"

    def _to_mapping(self, value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        return {}

    def _compact_value(self, value: Any) -> str:
        if isinstance(value, Mapping):
            return "；".join(
                f"{key}={self._compact_value(item)}" for key, item in value.items()
            )
        if isinstance(value, str):
            return value
        if isinstance(value, Sequence):
            return "，".join(self._compact_value(item) for item in value)
        return str(value)

    def _format_section(self, section: PromptSection) -> str:
        return f"## {section.layer.value}\n{section.content}"

    def _default_templates(self) -> dict[str, PromptTemplateSpec]:
        return {
            "global_system_v0_1": PromptTemplateSpec(
                id="global_system_v0_1",
                layer=PromptLayer.GLOBAL_SYSTEM,
                version="v0.1",
                filename="global_system_v0_1.txt",
            ),
            "persona_little_fox_v0_1": PromptTemplateSpec(
                id="persona_little_fox_v0_1",
                layer=PromptLayer.PERSONA,
                version="v0.1",
                filename="persona_little_fox_v0_1.txt",
            ),
            "scene_daily_after_school_checkin_v0_1": PromptTemplateSpec(
                id="scene_daily_after_school_checkin_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/daily_after_school_checkin_v0_1.txt",
            ),
            "scene_learning_homework_help_v0_1": PromptTemplateSpec(
                id="scene_learning_homework_help_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/learning_homework_help_v0_1.txt",
            ),
            "scene_daily_bedtime_reflection_v0_1": PromptTemplateSpec(
                id="scene_daily_bedtime_reflection_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/daily_bedtime_reflection_v0_1.txt",
            ),
            "scene_safety_guardian_v0_1": PromptTemplateSpec(
                id="scene_safety_guardian_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/safety_guardian_v0_1.txt",
            ),
            "scene_safety_gentle_checkin_v0_1": PromptTemplateSpec(
                id="scene_safety_gentle_checkin_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/safety_gentle_checkin_v0_1.txt",
            ),
            "scene_privacy_boundary_v0_1": PromptTemplateSpec(
                id="scene_privacy_boundary_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/privacy_boundary_v0_1.txt",
            ),
            "output_contract_child_chat_v0_1": PromptTemplateSpec(
                id="output_contract_child_chat_v0_1",
                layer=PromptLayer.OUTPUT_CONTRACT,
                version="v0.1",
                filename="output_contracts/child_chat_v0_1.txt",
            ),
        }

    def _default_scene_templates(self) -> dict[str, str]:
        return {
            "daily.after_school_checkin": "scene_daily_after_school_checkin_v0_1",
            "learning.homework_help": "scene_learning_homework_help_v0_1",
            "daily.bedtime_reflection": "scene_daily_bedtime_reflection_v0_1",
            "safety.guardian": "scene_safety_guardian_v0_1",
            "safety.gentle_checkin": "scene_safety_gentle_checkin_v0_1",
            "privacy.boundary": "scene_privacy_boundary_v0_1",
        }


_prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    return _prompt_manager
