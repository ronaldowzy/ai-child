from fastapi import FastAPI

from app.api.v1.conversation import router as conversation_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)

app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(conversation_router, prefix=settings.api_v1_prefix)
