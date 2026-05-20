from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import wave

from app.domain.tts import TtsProviderName, TtsVoiceVersion


class TtsCacheService:
    def __init__(self, *, cache_dir: Path) -> None:
        self._cache_dir = cache_dir

    def normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def voice_sample_sha256(self, voice_sample_path: Path) -> str:
        digest = hashlib.sha256()
        with voice_sample_path.open("rb") as audio_file:
            for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def cache_key(
        self,
        *,
        normalized_text: str,
        emotion: str,
        voice_version: TtsVoiceVersion,
        provider: TtsProviderName,
        model: str,
        voice_sample_sha256: str,
        prompt_version: str,
    ) -> str:
        payload = "|".join(
            [
                normalized_text,
                emotion,
                voice_version.value,
                provider.value,
                model,
                voice_sample_sha256,
                prompt_version,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def audio_path(self, *, voice_version: TtsVoiceVersion, cache_key: str) -> Path:
        return self._voice_dir(voice_version) / f"{cache_key}.wav"

    def metadata_path(self, *, voice_version: TtsVoiceVersion, cache_key: str) -> Path:
        return self._voice_dir(voice_version) / f"{cache_key}.json"

    def has(
        self,
        *,
        voice_version: TtsVoiceVersion,
        cache_key: str,
    ) -> bool:
        return self.audio_path(voice_version=voice_version, cache_key=cache_key).exists()

    def load_metadata(
        self,
        *,
        voice_version: TtsVoiceVersion,
        cache_key: str,
    ) -> dict[str, object]:
        path = self.metadata_path(voice_version=voice_version, cache_key=cache_key)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as metadata_file:
            loaded = json.load(metadata_file)
        return loaded if isinstance(loaded, dict) else {}

    def save(
        self,
        *,
        voice_version: TtsVoiceVersion,
        cache_key: str,
        audio_bytes: bytes,
        metadata: dict[str, object],
    ) -> Path:
        voice_dir = self._voice_dir(voice_version)
        voice_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.audio_path(voice_version=voice_version, cache_key=cache_key)
        metadata_path = self.metadata_path(
            voice_version=voice_version,
            cache_key=cache_key,
        )
        audio_path.write_bytes(audio_bytes)
        with metadata_path.open("w", encoding="utf-8") as metadata_file:
            json.dump(
                {
                    **metadata,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "cacheHit": False,
                },
                metadata_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        return audio_path

    def duration_seconds(self, audio_path: Path) -> float | None:
        try:
            with wave.open(str(audio_path), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                if frame_rate <= 0:
                    return None
                return wav_file.getnframes() / frame_rate
        except (wave.Error, OSError):
            return None

    def _voice_dir(self, voice_version: TtsVoiceVersion) -> Path:
        return self._cache_dir / voice_version.value
