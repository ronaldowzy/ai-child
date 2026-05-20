from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TtsEmotion(StrEnum):
    ENCOURAGE = "encourage"
    COMFORT = "comfort"
    HINT = "hint"
    EXPLAIN = "explain"
    HAPPY = "happy"
    CALM = "calm"
    SAFETY = "safety"
    PRIVACY = "privacy"


class TtsProviderName(StrEnum):
    MOCK = "mock"
    MIMO = "mimo"


class TtsVoiceVersion(StrEnum):
    XIAOBAIHU_V01 = "xiaobaohu_v01"


class TtsProviderRequest(BaseModel):
    text: str
    emotion: TtsEmotion
    voice_version: TtsVoiceVersion
    voice_sample_path: str
    voice_sample_sha256: str
    style_prompt: str
    prompt_version: str = "v01"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TtsProviderResult(BaseModel):
    audio_bytes: bytes
    audio_format: str = "wav"
    content_type: str = "audio/wav"
    duration: float | None = None
    provider: TtsProviderName
    model: str
    metadata: dict[str, Any] = Field(default_factory=dict)


XIAOBAIHU_TTS_PROMPT_VERSION = "v01"

XIAOBAIHU_BASE_VOICE_STYLE_PROMPT = (
    "小白狐 AI 伙伴的角色声音。语气清亮、轻快、灵动、亲近，"
    "像一只聪明的小白狐在陪孩子学习。说话有微笑感，尾音轻轻上扬，"
    "节奏自然活泼，不要沉闷，不要成人化，不要像老师讲课，不要播音腔，"
    "不要客服感。遇到孩子答错时轻轻安慰，答对时开心表扬，"
    "提示时像发现了一个小线索。"
)

XIAOBAIHU_EMOTION_PROMPTS: dict[TtsEmotion, str] = {
    TtsEmotion.ENCOURAGE: "轻快、温暖、鼓励，像看到孩子刚刚完成了一小步。",
    TtsEmotion.COMFORT: "轻声、耐心、安慰，语速稍慢，像陪孩子慢慢平静下来。",
    TtsEmotion.HINT: "俏皮、聪明、像发现了一个小线索，但不要吊胃口。",
    TtsEmotion.EXPLAIN: "清楚、自然、轻快，不要像老师讲课，不要播音腔。",
    TtsEmotion.HAPPY: "开心、有微笑感，尾音轻轻上扬，但不要尖叫或过度兴奋。",
    TtsEmotion.CALM: "安静、柔和、低刺激，适合睡前或孩子不想说话时。",
    TtsEmotion.SAFETY: "稳定、认真、温和，不恐吓孩子，不戏剧化。",
    TtsEmotion.PRIVACY: "温和但清晰，像提醒孩子先停一下，不责备。",
}


def xiaobaihu_style_prompt(emotion: TtsEmotion) -> str:
    return (
        f"{XIAOBAIHU_BASE_VOICE_STYLE_PROMPT}\n"
        f"当前情绪：{emotion.value}。"
        f"{XIAOBAIHU_EMOTION_PROMPTS[emotion]}"
    )
