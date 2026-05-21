from fastapi import APIRouter, HTTPException, status

from app.domain.schemas.asr import AsrTranscriptionRequest, AsrTranscriptionResponse
from app.providers.asr.base import (
    AsrProviderError,
    AsrProviderHttpError,
    AsrProviderTimeoutError,
)
from app.services.asr_data_policy_guard import AsrDataPolicyBlockedError
from app.services.asr_service import AsrRequestValidationError, AsrService

router = APIRouter(prefix="/asr", tags=["asr"])


@router.post(
    "/transcribe",
    response_model=AsrTranscriptionResponse,
    response_model_by_alias=True,
)
def transcribe_asr(
    request: AsrTranscriptionRequest,
) -> AsrTranscriptionResponse:
    try:
        return AsrService().transcribe(request)
    except AsrRequestValidationError as exc:
        http_status = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if exc.error_code == "audio_too_large"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=http_status, detail=exc.error_code) from exc
    except AsrDataPolicyBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AsrProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="provider_timeout",
        ) from exc
    except AsrProviderHttpError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="provider_http_error",
        ) from exc
    except AsrProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="provider_error",
        ) from exc
