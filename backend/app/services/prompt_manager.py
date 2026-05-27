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
from app.services.age_band_policy import derive_age_band_reply_policy


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
        time_context: Any | None = None,
        image_context: Mapping[str, Any] | Any | None = None,
        turn_guidance_context: Mapping[str, Any] | Any | None = None,
        memory_context: Sequence[Any] | Mapping[str, Any] | str | None = None,
        persona_template_id: str | None = None,
        output_contract_template_id: str | None = None,
    ) -> ComposedPrompt:
        sections = [
            self._load_template_section(self._global_system_template_id),
            self._load_template_section(
                persona_template_id or self._persona_template_id
            ),
            self._build_child_profile_section(parent_policy),
            self._build_parent_message_section(parent_policy),
            self._build_parent_policy_section(parent_policy),
            self._build_time_context_section(time_context),
            self._build_image_context_section(image_context),
            self._load_scene_section(scene_id),
            self._build_turn_guidance_section(turn_guidance_context),
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

    def _build_child_profile_section(self, parent_policy: Any | None) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.CHILD_PROFILE,
            template_id="child_profile_runtime",
            version=self._runtime_version(parent_policy),
            filename=None,
            content=self._render_child_profile(parent_policy),
        )

    def _build_parent_message_section(self, parent_policy: Any | None) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.PARENT_MESSAGE,
            template_id="parent_message_runtime",
            version=self._runtime_version(parent_policy),
            filename=None,
            content=self._render_parent_message(parent_policy),
        )

    def _build_time_context_section(self, time_context: Any | None) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.TIME_CONTEXT,
            template_id="time_context_runtime",
            version="runtime",
            filename=None,
            content=self._render_time_context(time_context),
        )

    def _build_image_context_section(
        self,
        image_context: Mapping[str, Any] | Any | None,
    ) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.IMAGE_CONTEXT,
            template_id="image_context_runtime",
            version="runtime",
            filename=None,
            content=self._render_image_context(image_context),
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

    def _build_turn_guidance_section(
        self,
        turn_guidance_context: Mapping[str, Any] | Any | None,
    ) -> PromptSection:
        return PromptSection(
            layer=PromptLayer.TURN_GUIDANCE,
            template_id="turn_guidance_runtime",
            version="runtime",
            filename=None,
            content=self._render_turn_guidance(turn_guidance_context),
        )

    def _render_parent_policy(self, parent_policy: Any | None) -> str:
        if parent_policy is None:
            return "家长当前没有提供额外规则。继续遵守全局安全底线。"
        if isinstance(parent_policy, str):
            return parent_policy.strip()

        data = self._to_mapping(parent_policy)
        if not data:
            return "家长当前没有提供额外规则。继续遵守全局安全底线。"

        lines = ["家长规则："]
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

    _TEMPERAMENT_LABELS = {
        "warms_up_slowly": "慢热，需要一点时间",
        "expressive": "爱表达，话比较多",
        "concise": "说话短，需要小选择",
        "imaginative": "爱想象/编故事",
        "active": "喜欢运动和动手",
        "sensitive_to_pressure": "不喜欢被追问或催促",
        "easily_frustrated": "遇到困难容易急",
        "curious": "爱问为什么",
    }

    _SUPPORT_STYLE_LABELS = {
        "offer_two_choices": "多给二选一",
        "ask_fewer_questions": "少追问",
        "encourage_gently": "多温和鼓励",
        "slow_down_explanations": "解释慢一点",
        "use_shorter_sentences": "句子短一点",
        "invite_show_and_tell": "多鼓励展示作品/物品",
        "avoid_competition_framing": "少用输赢/排名框架",
    }

    _LEARNING_SUPPORT_LABELS = {
        "hint_first": "先提示，不直接给答案",
        "ask_what_child_knows": "先问孩子知道什么",
        "use_examples": "用例子解释",
        "keep_homework_short": "作业帮助要短",
    }

    _GENDER_LABELS = {
        "boy": "男孩",
        "girl": "女孩",
        "prefer_not_to_say": "不填写",
        "custom": "自定义称呼",
    }

    def _render_child_profile(self, parent_policy: Any | None) -> str:
        data = self._to_mapping(parent_policy) if parent_policy is not None else {}
        raw_message = str(data.get("parent_message_raw") or "").strip()
        nickname = str(data.get("child_nickname") or "").strip()
        display_name = str(data.get("child_display_name") or "").strip()
        communication_preferences = data.get("communication_preferences")
        preferences = (
            dict(communication_preferences)
            if isinstance(communication_preferences, Mapping)
            else {}
        )
        child_age = self._compact_profile_scalar(preferences.get("child_age"))
        child_grade = self._compact_profile_scalar(preferences.get("child_grade"))
        child_gender = self._compact_profile_scalar(preferences.get("child_gender"))
        call_preference = self._compact_profile_scalar(
            preferences.get("child_call_preference")
        )
        child_interests = self._profile_string_list(preferences.get("child_interests"))
        topic_boundaries = self._profile_string_list(preferences.get("topic_boundaries"))
        temperament = self._profile_string_list(preferences.get("child_temperament"))
        support_style = self._profile_string_list(
            preferences.get("support_style_preferences")
        )
        learning_support = self._profile_string_list(
            preferences.get("learning_support_preferences")
        )
        age_policy = derive_age_band_reply_policy(parent_policy)
        age_lines = [
            "年龄与回复节奏是内部提示，不要直接说给孩子：",
            f"- age_band: {age_policy.age_band}",
            f"- reply_char_budget: {age_policy.reply_char_budget}",
            f"- question_policy: {age_policy.question_policy}",
        ]
        profile_lines: list[str] = []
        if nickname:
            profile_lines.append(f"- child_nickname: {nickname}")
        if display_name:
            profile_lines.append(f"- child_display_name: {display_name}")
        if child_age:
            profile_lines.append(f"- child_age: {child_age}")
        if child_grade:
            profile_lines.append(f"- child_grade: {child_grade}")
        if child_gender and child_gender not in ("unknown", "未设置"):
            gender_label = self._GENDER_LABELS.get(child_gender, child_gender)
            profile_lines.append(
                f"- child_gender: {gender_label}。"
                "只用于尊重称呼和措辞，不推断性格、能力、兴趣或偏好。"
            )
        if call_preference:
            profile_lines.append(
                "- child_call_preference: "
                f"{call_preference}。只用于尊重称呼和措辞，不推断性格、能力或兴趣。"
            )
        if child_interests:
            profile_lines.append(
                "- child_interests: "
                f"{'，'.join(child_interests[:8])}。这是可尝试的轻话题，不要变成任务。"
            )
        if topic_boundaries:
            profile_lines.append(
                "- topic_boundaries: "
                f"{'，'.join(topic_boundaries[:8])}。孩子不想聊时优先尊重，不拉回旧话题。"
            )
        if temperament:
            labels = [self._TEMPERAMENT_LABELS.get(t, t) for t in temperament[:6]]
            profile_lines.append(
                "- child_temperament: "
                f"{'，'.join(labels)}。"
                "这些是家长提供的背景参考，不要给孩子贴标签或直接说出来。"
            )
        if support_style:
            labels = [self._SUPPORT_STYLE_LABELS.get(s, s) for s in support_style[:5]]
            profile_lines.append(
                "- support_style_preferences: "
                f"{'，'.join(labels)}。"
                "在回复中自然体现这些支持方式，不要告诉孩子家长设置了这些偏好。"
            )
        if learning_support:
            labels = [
                self._LEARNING_SUPPORT_LABELS.get(s, s)
                for s in learning_support[:4]
            ]
            profile_lines.append(
                "- learning_support_preferences: "
                f"{'，'.join(labels)}。"
                "在学习帮助场景中自然体现这些方式。"
            )

        if not raw_message and not profile_lines:
            return "\n".join(
                [
                    "当前没有单独的孩子画像。不要编造孩子的小名、性格或家庭信息。",
                    *age_lines,
                ]
            )
        lines = [
            "孩子画像来自结构化家长设置和家长寄语的背景信息。可以用它理解孩子的兴趣、近期状态和沟通节奏；不要把它当成固定标签，也不要编造寄语中没有的事实。"
        ]
        lines.extend(profile_lines)
        lines.extend(age_lines)
        return "\n".join(lines)

    def _render_parent_message(self, parent_policy: Any | None) -> str:
        data = self._to_mapping(parent_policy) if parent_policy is not None else {}
        raw_message = str(data.get("parent_message_raw") or "").strip()
        name_rules = [
            "称呼规则：有 child_nickname 时优先使用小名；没有小名再使用 child_display_name；都没有则不强行称呼。",
            "小名适合用于开场、情绪接住、鼓励、换话题和睡前收尾；普通连续对话中每 3-5 轮自然出现一次即可，不要每轮都叫小名。",
            "不要用小名制造亲密依赖，例如“只有小白狐懂你”。",
        ]
        if not raw_message:
            return "\n".join(
                [
                    "家长暂未提供自由寄语。继续遵守全局安全底线和结构化家长规则。",
                    *name_rules,
                ]
            )
        return "\n".join(
            [
                "以下内容是家长给小白狐的自由寄语，可能包含孩子小名、性格特点、近期情况和希望的引导方式。",
                "请把它作为理解孩子的背景，而不是机械复述给孩子；不要直接对孩子说“你家长说你……”。",
                "如果寄语包含“胆小、懒、不主动、不聪明”等负面标签，只能转化为支持性、低压力的表达，不得照搬给孩子。",
                *name_rules,
                "家长寄语不能覆盖儿童安全底线，不能要求你替孩子保密，不能诱导孩子透露隐私或监控孩子。",
                "<parent_message_raw>",
                raw_message,
                "</parent_message_raw>",
            ]
        )

    def _render_time_context(self, time_context: Any | None) -> str:
        if time_context is None:
            return "当前没有设备时间上下文。不要因为缺少时间而强行猜测孩子状态。"
        data = self._to_mapping(time_context)
        if not data:
            return "当前没有可解析的设备时间上下文。"
        period = data.get("time_period") or data.get("period") or "unknown"
        lines = [
            f"当前时间段：{period}。",
            "时间段只用于开场问候、语气和轻量提醒，不是固定模式或菜单。",
            "如果孩子主动提出自由话题，优先顺着话题自然交流。",
        ]
        if period == "bedtime":
            lines.append("睡前语气应更短、更安静、低刺激；只有孩子明确说晚安、困了或要睡觉时，才进入睡前收尾。")
        if period == "after_school":
            lines.append("放学后语气可以轻松低压力，但不要默认强迫孩子汇报学校。")
        return "\n".join(lines)

    def _render_image_context(self, image_context: Mapping[str, Any] | Any | None) -> str:
        if image_context is None:
            return (
                "当前没有图片上下文。不要假装看到了图片。"
                "如果孩子只是说想拍照给你看，请告诉孩子可以点“拍给小白狐看”上传。"
            )
        data = self._to_mapping(image_context)
        if not data:
            return (
                "当前没有图片上下文。不要假装看到了图片。"
                "如果孩子只是说想拍照给你看，请告诉孩子可以点“拍给小白狐看”上传。"
            )

        text = str(data.get("recognized_text") or data.get("text") or "").strip()
        child_caption = str(data.get("child_caption") or "").strip()
        purpose = str(data.get("image_purpose") or "unknown")
        recognized_type = str(data.get("recognized_type") or "unknown")

        lines = [
            "孩子刚刚分享了一张图片。以下内容是系统提供的安全图片摘要，不是原始图片本身。",
            "你可以基于这段摘要自然回应；不要说你看不到图片、不能看图片或没有看图功能。",
            f"图片意图：{purpose}。",
            f"识别类型：{recognized_type}。",
        ]
        if text:
            lines.append(f"图片描述：{text}")
        if child_caption:
            lines.append(f"孩子说明：{child_caption}")
        lines.append("这段图片描述只用于帮助你回应，不要逐字复述给孩子，也不要展开成识别报告。")
        lines.append("最多提及一个具体、安全、被摘要支持的细节。不要编造摘要里没有的内容。")
        if recognized_type == "homework_problem":
            lines.append(
                "如果孩子是在问图片里的题目，请先引导孩子复述题意或说出卡点；"
                "不要直接给最终答案。"
            )
        elif recognized_type in ("child_drawing", "art_feedback"):
            lines.append(
                "如果是孩子的画或手工作品，注意到一个具体细节就好，不要打分、比较或纠正。"
                "可以邀请孩子说说这个部分的故事或名字。"
            )
        elif recognized_type in ("toy", "object", "handmade", "daily_life"):
            lines.append(
                "如果是玩具、物品或日常场景，提到一个具体细节，"
                "然后问孩子最想让小白狐看哪里。"
            )
        elif recognized_type == "privacy_sensitive":
            lines.append(
                "如果图片可能包含隐私内容，不要描述私密细节。可以建议孩子请家长一起看一下。"
            )
        lines.append("如果孩子没有说这是作业题，请自然围绕图片继续聊，不要把它强行当成作业。")
        return "\n".join(lines)

    def _render_turn_guidance(
        self,
        turn_guidance_context: Mapping[str, Any] | Any | None,
    ) -> str:
        if turn_guidance_context is None:
            return "本轮没有额外动态提示。继续遵守场景提示、儿童安全底线和输出契约。"

        data = self._to_mapping(turn_guidance_context)
        hints = data.get("hints")
        guidance = data.get("guidance")
        recent_topic = str(data.get("recent_topic") or "").strip()
        same_topic_score = data.get("same_topic_score")
        same_topic_turn_count = data.get("same_topic_turn_count")
        engagement = str(data.get("child_engagement_signal") or "").strip()
        topic_shift_recommended = data.get("topic_shift_recommended") is True
        topic_shift_reason = str(data.get("topic_shift_reason") or "").strip()
        suggested_topic_seeds = data.get("suggested_topic_seeds")

        if not isinstance(hints, Sequence) or isinstance(hints, str) or not hints:
            return "本轮没有额外动态提示。继续遵守场景提示、儿童安全底线和输出契约。"

        lines = ["本轮动态提示："]
        if recent_topic:
            lines.append(f"- recent_topic: 最近可能围绕“{recent_topic}”展开。")
        if isinstance(same_topic_score, int) and same_topic_score > 0:
            lines.append(f"- same_topic_score: {same_topic_score}")
        if isinstance(same_topic_turn_count, int) and same_topic_turn_count > 0:
            lines.append(f"- same_topic_turn_count: {same_topic_turn_count}")
        if engagement:
            lines.append(f"- child_engagement_signal: {engagement}")
        if topic_shift_recommended:
            lines.append("- topic_shift_recommended: true")
        if topic_shift_reason:
            lines.append(f"- topic_shift_reason: {topic_shift_reason}")
        if (
            isinstance(suggested_topic_seeds, Sequence)
            and not isinstance(suggested_topic_seeds, str)
            and suggested_topic_seeds
        ):
            seeds = [
                str(seed).strip()
                for seed in suggested_topic_seeds
                if str(seed).strip()
            ]
            if seeds:
                lines.append(f"- suggested_topic_seeds: {'，'.join(seeds[:4])}")

        guidance_map = guidance if isinstance(guidance, Mapping) else {}
        for hint in hints:
            hint_name = str(hint)
            instruction = str(guidance_map.get(hint_name) or "").strip()
            if instruction:
                lines.append(f"- {hint_name}: {instruction}")
            else:
                lines.append(f"- {hint_name}: 结合当前儿童语音上下文，降低误判和过度追问。")
        lines.append("这些动态提示是内部提示，不要暴露给孩子。")
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

    def _compact_profile_scalar(self, value: Any) -> str:
        if value is None or isinstance(value, bool):
            return ""
        text = str(value).strip()
        if not text:
            return ""
        return text[:80]

    def _profile_string_list(self, value: Any) -> list[str]:
        if isinstance(value, str):
            source = value.replace("，", "\n").replace("、", "\n").replace(",", "\n")
            items = source.splitlines()
        elif isinstance(value, Sequence):
            items = [str(item) for item in value if item is not None]
        else:
            return []
        cleaned = []
        for item in items:
            text = " ".join(item.strip().split())
            if text:
                cleaned.append(text[:60])
        return cleaned

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
            "scene_conversation_open_v0_1": PromptTemplateSpec(
                id="scene_conversation_open_v0_1",
                layer=PromptLayer.SCENE,
                version="v0.1",
                filename="scenes/conversation_open_v0_1.txt",
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
            "conversation.open": "scene_conversation_open_v0_1",
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
