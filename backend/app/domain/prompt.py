from enum import StrEnum

from pydantic import BaseModel, Field


class PromptLayer(StrEnum):
    GLOBAL_SYSTEM = "global_system"
    PERSONA = "persona"
    CHILD_PROFILE = "child_profile"
    PARENT_MESSAGE = "parent_message"
    PARENT_POLICY = "parent_policy"
    TIME_CONTEXT = "time_context"
    IMAGE_CONTEXT = "image_context"
    SCENE = "scene"
    TURN_GUIDANCE = "turn_guidance"
    MEMORY_CONTEXT = "memory_context"
    OUTPUT_CONTRACT = "output_contract"


class PromptTemplateSpec(BaseModel):
    id: str = Field(..., min_length=1)
    layer: PromptLayer
    version: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)


class PromptVersion(BaseModel):
    layer: PromptLayer
    template_id: str
    version: str
    filename: str | None = None


class PromptSection(BaseModel):
    layer: PromptLayer
    template_id: str
    version: str
    content: str
    filename: str | None = None


class ComposedPrompt(BaseModel):
    scene_id: str
    prompt: str
    sections: list[PromptSection] = Field(default_factory=list)
    prompt_versions: dict[str, PromptVersion] = Field(default_factory=dict)
    prompt_total_chars: int = 0
    section_chars_by_layer: dict[str, int] = Field(default_factory=dict)
    prompt_template_mode: str = "full"

    @property
    def content(self) -> str:
        return self.prompt
