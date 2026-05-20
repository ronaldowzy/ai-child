from fastapi import FastAPI

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

app.include_router(tts_media_router)
app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(conversation_router, prefix=settings.api_v1_prefix)
app.include_router(conversation_attachment_router, prefix=settings.api_v1_prefix)
app.include_router(parent_policy_router, prefix=settings.api_v1_prefix)
app.include_router(parent_report_router, prefix=settings.api_v1_prefix)
app.include_router(memories_router, prefix=settings.api_v1_prefix)
app.include_router(tts_router, prefix=settings.api_v1_prefix)
