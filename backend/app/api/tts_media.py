from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.domain.tts import TtsVoiceVersion

router = APIRouter()


@router.get("/media/tts/{voice_version}/{filename}")
def get_tts_audio(voice_version: str, filename: str) -> FileResponse:
    try:
        normalized_voice_version = TtsVoiceVersion(voice_version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc

    if not filename.endswith(".wav") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    settings = get_settings()
    cache_dir = settings.resolve_repo_path(settings.tts_cache_dir)
    audio_path = (
        cache_dir / normalized_voice_version.value / Path(filename).name
    ).resolve()
    allowed_root = (cache_dir / normalized_voice_version.value).resolve()
    if allowed_root not in audio_path.parents or not audio_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(path=audio_path, media_type="audio/wav")
