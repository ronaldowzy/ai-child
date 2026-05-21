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
from app.middleware.request_id import RequestIdMiddleware, get_request_id

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
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "request_failed",
            extra={
                "event": "request_failed",
                "request_id": get_request_id(),
                "method": request.method,
                "path": request.url.path,
                "status_code": None,
                "elapsed_ms": round(elapsed_ms, 1),
                "child_id_hash": None,
                "session_id_hash": None,
                "provider": None,
                "model": None,
                "error_type": exc.__class__.__name__,
            },
        )
        raise
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "request_finished",
        extra={
            "event": "request_finished",
            "request_id": get_request_id(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed_ms, 1),
            "child_id_hash": None,
            "session_id_hash": None,
            "provider": None,
            "model": None,
            "error_type": None,
        },
    )
    return response

app.add_middleware(RequestIdMiddleware)

app.include_router(tts_media_router)
app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(conversation_router, prefix=settings.api_v1_prefix)
app.include_router(conversation_attachment_router, prefix=settings.api_v1_prefix)
app.include_router(parent_policy_router, prefix=settings.api_v1_prefix)
app.include_router(parent_report_router, prefix=settings.api_v1_prefix)
app.include_router(memories_router, prefix=settings.api_v1_prefix)
app.include_router(tts_router, prefix=settings.api_v1_prefix)
