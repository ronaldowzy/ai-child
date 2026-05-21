from fastapi import APIRouter

from app.services.health_service import HealthService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/detail")
def health_detail() -> dict[str, object]:
    return HealthService().detail()
