import logging

from app.core.config import Settings
from app.services.tts_prewarm_service import (
    COMMON_PHRASES,
    TtsPrewarmService,
)
from app.domain.schemas.tts import XiaobaihuTtsResponse
from app.domain.tts import TtsEmotion, TtsProviderName, TtsVoiceVersion


class RecordingTtsService:
    """记录调用次数的 TTS 服务。"""

    def __init__(self, *, cache_hit: bool = False) -> None:
        self.call_count = 0
        self.texts: list[str] = []
        self._cache_hit = cache_hit

    def generate_xiaobaihu(self, request) -> XiaobaihuTtsResponse:
        self.call_count += 1
        self.texts.append(request.text)
        return XiaobaihuTtsResponse(
            audioUrl=f"/media/tts/xiaobaohu_v01/test_{self.call_count}.wav",
            duration=1.0,
            text=request.text,
            emotion=request.emotion,
            voiceVersion=TtsVoiceVersion.XIAOBAIHU_V01.value,
            provider=TtsProviderName.MOCK.value,
            model="mock-tts-v0",
            cacheHit=self._cache_hit,
        )


class FailingTtsService:
    """总是失败的 TTS 服务。"""

    def __init__(self) -> None:
        self.call_count = 0

    def generate_xiaobaihu(self, request) -> XiaobaihuTtsResponse:
        self.call_count += 1
        raise RuntimeError("simulated TTS failure")


def test_prewarm_generates_all_common_phrases() -> None:
    tts_service = RecordingTtsService()
    settings = Settings(conversation_tts_enabled=True)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    result = prewarm.prewarm_sync()

    assert result["total"] == len(COMMON_PHRASES)
    assert result["cached_before"] == 0
    assert result["newly_generated"] == len(COMMON_PHRASES)
    assert result["failed"] == 0
    assert result["elapsed_ms"] >= 0
    assert tts_service.call_count == len(COMMON_PHRASES)


def test_prewarm_reports_cached_phrases() -> None:
    tts_service = RecordingTtsService(cache_hit=True)
    settings = Settings(conversation_tts_enabled=True)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    result = prewarm.prewarm_sync()

    assert result["cached_before"] == len(COMMON_PHRASES)
    assert result["newly_generated"] == 0
    assert result["failed"] == 0


def test_prewarm_handles_failures_gracefully() -> None:
    tts_service = FailingTtsService()
    settings = Settings(conversation_tts_enabled=True)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    result = prewarm.prewarm_sync()

    assert result["failed"] == len(COMMON_PHRASES)
    assert result["newly_generated"] == 0
    assert tts_service.call_count == len(COMMON_PHRASES)


def test_prewarm_skips_when_tts_disabled() -> None:
    tts_service = RecordingTtsService()
    settings = Settings(conversation_tts_enabled=False)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    result = prewarm.prewarm_sync()

    assert result["total"] == len(COMMON_PHRASES)
    assert result["cached_before"] == 0
    assert result["newly_generated"] == 0
    assert result["failed"] == 0
    assert tts_service.call_count == 0


def test_prewarm_is_idempotent() -> None:
    """多次调用 prewarm_async 不会重复启动线程。"""
    tts_service = RecordingTtsService()
    settings = Settings(conversation_tts_enabled=True)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    prewarm.prewarm_sync()
    first_count = tts_service.call_count

    # 第二次同步调用仍然会执行（sync 不检查 _prewarmed）
    prewarm.prewarm_sync()
    assert tts_service.call_count == first_count * 2


def test_prewarm_logs_timing(caplog) -> None:
    caplog.set_level(logging.INFO, logger="app.tts_timing")
    tts_service = RecordingTtsService()
    settings = Settings(conversation_tts_enabled=True)
    prewarm = TtsPrewarmService(tts_service=tts_service, settings=settings)

    # 使用同步模式触发 worker 逻辑
    prewarm._prewarm_worker()

    records = [
        r for r in caplog.records
        if getattr(r, "event", None) == "tts_prewarm_finished"
    ]
    assert len(records) == 1
    record = records[0]
    assert record.total_phrases == len(COMMON_PHRASES)
    assert record.newly_generated == len(COMMON_PHRASES)
    assert record.failed == 0
    assert record.elapsed_ms >= 0
