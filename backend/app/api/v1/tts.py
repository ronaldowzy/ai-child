from fastapi import APIRouter, HTTPException, status

from app.domain.schemas.tts import XiaobaihuTtsRequest, XiaobaihuTtsResponse
from app.providers.tts.base import TtsProviderError
from app.services.tts_data_policy_guard import TtsDataPolicyBlockedError
from app.services.tts_service import (
    TtsRequestValidationError,
    TtsService,
    TtsVoiceSampleMissingError,
)

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post(
    "/xiaobaohu",
    response_model=XiaobaihuTtsResponse,
    response_model_by_alias=True,
)
def generate_xiaobaihu_tts(request: XiaobaihuTtsRequest) -> XiaobaihuTtsResponse:
    try:
        return TtsService().generate_xiaobaihu(request)
    except TtsRequestValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except TtsVoiceSampleMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except TtsDataPolicyBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except TtsProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
