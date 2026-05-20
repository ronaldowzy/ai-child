import logging
import time

from fastapi import FastAPI
from fastapi import Request

from app.api.v1.conversation_attachment import router as conversation_attachment_router
from app.api.v1.conversation import router as conversation_router
from app.api.v1.health import router as health_router
from app.api.v1.memories import router as memories_router
from app.api.v1.parent_report import router as parent_report_router
from app.api.v1.parent_policy import router as parent_policy_router
from app.api.v1.tts import router as tts_router
from app.api.tts_media import router as tts_media_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()
tts_cache_dir = settings.resolve_repo_path(settings.tts_cache_dir)
tts_cache_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)
logger = logging.getLogger("app.request_timing")


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "request_failed method=%s path=%s elapsed_ms=%.1f",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "request_finished method=%s path=%s status=%s elapsed_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

app.include_router(tts_media_router)
app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(conversation_router, prefix=settings.api_v1_prefix)
app.include_router(conversation_attachment_router, prefix=settings.api_v1_prefix)
app.include_router(parent_policy_router, prefix=settings.api_v1_prefix)
app.include_router(parent_report_router, prefix=settings.api_v1_prefix)
app.include_router(memories_router, prefix=settings.api_v1_prefix)
app.include_router(tts_router, prefix=settings.api_v1_prefix)
