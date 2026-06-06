"""常见短句 TTS 预热服务。

在后台为高频短句预先生成 TTS 缓存，减少孩子首次听到语音的等待。
"""

import logging
import threading
import time

from app.core.config import Settings, get_settings
from app.domain.schemas.tts import XiaobaihuTtsRequest
from app.domain.tts import TtsVoiceVersion
from app.services.tts_service import TtsService, get_tts_service


# 常见短句 + 对应情绪，按儿童场景分组
# 这些短句来自小白狐提示语规范中 1-3 句短句的典型场景
COMMON_PHRASES: list[tuple[str, str]] = [
    # 打招呼
    ("你好呀！", "encourage"),
    ("我是小白狐。", "encourage"),
    ("很高兴认识你！", "happy"),
    # 鼓励
    ("你做得真棒！", "encourage"),
    ("加油，你可以的！", "encourage"),
    ("没关系，我们再试一次。", "comfort"),
    # 安全
    ("这个要告诉爸爸妈妈哦。", "safety"),
    ("我们不告诉陌生人。", "safety"),
    # 学习
    ("我们一起想想看。", "hint"),
    ("你先试试看？", "hint"),
    # 睡前
    ("晚安，做个好梦。", "calm"),
    ("我们明天再聊吧。", "calm"),
]


class TtsPrewarmService:
    """后台预热常见短句的 TTS 缓存。"""

    def __init__(
        self,
        *,
        tts_service: TtsService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._tts_service = tts_service or get_tts_service()
        self._settings = settings or get_settings()
        self._lock = threading.Lock()
        self._prewarmed = False
        self._prewarm_thread: threading.Thread | None = None

    @property
    def is_prewarmed(self) -> bool:
        with self._lock:
            return self._prewarmed

    def prewarm_async(self) -> None:
        """在后台线程中预热 TTS 缓存，不阻塞调用方。"""
        with self._lock:
            if self._prewarmed or self._prewarm_thread is not None:
                return
            self._prewarm_thread = threading.Thread(
                target=self._prewarm_worker,
                name="tts-prewarm",
                daemon=True,
            )
            self._prewarm_thread.start()

    def prewarm_sync(self) -> dict[str, object]:
        """同步预热，返回统计信息。用于测试或手动触发。"""
        return self._do_prewarm()

    def _prewarm_worker(self) -> None:
        try:
            result = self._do_prewarm()
            logging.getLogger("app.tts_timing").info(
                "tts_prewarm_finished",
                extra={
                    "event": "tts_prewarm_finished",
                    "total_phrases": result["total"],
                    "cached_before": result["cached_before"],
                    "newly_generated": result["newly_generated"],
                    "failed": result["failed"],
                    "elapsed_ms": result["elapsed_ms"],
                },
            )
        except Exception as exc:
            logging.getLogger("app.tts_timing").warning(
                "tts_prewarm_failed",
                extra={
                    "event": "tts_prewarm_failed",
                    "error_type": exc.__class__.__name__,
                },
            )
        finally:
            with self._lock:
                self._prewarmed = True
                self._prewarm_thread = None

    def _do_prewarm(self) -> dict[str, object]:
        """执行预热，返回统计。"""
        started_at = time.perf_counter()
        cached_before = 0
        newly_generated = 0
        failed = 0

        for text, emotion in COMMON_PHRASES:
            if not self._settings.conversation_tts_enabled:
                break
            try:
                request = XiaobaihuTtsRequest(
                    text=text,
                    emotion=emotion,
                    voiceVersion=TtsVoiceVersion.XIAOBAIHU_V01.value,
                    forceRefresh=False,
                )
                response = self._tts_service.generate_xiaobaihu(request)
                if response.cache_hit:
                    cached_before += 1
                else:
                    newly_generated += 1
            except Exception:
                failed += 1

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1)
        return {
            "total": len(COMMON_PHRASES),
            "cached_before": cached_before,
            "newly_generated": newly_generated,
            "failed": failed,
            "elapsed_ms": elapsed_ms,
        }


_prewarm_service: TtsPrewarmService | None = None


def get_tts_prewarm_service() -> TtsPrewarmService:
    global _prewarm_service
    if _prewarm_service is None:
        _prewarm_service = TtsPrewarmService()
    return _prewarm_service
