from pathlib import Path

from app.domain.tts import TtsProviderName, TtsVoiceVersion
from app.services.tts_cache_service import TtsCacheService


def test_tts_cache_key_changes_with_voice_sample_hash(tmp_path: Path) -> None:
    service = TtsCacheService(cache_dir=tmp_path / "cache")

    key_a = service.cache_key(
        normalized_text="你好。",
        emotion="encourage",
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        provider=TtsProviderName.MOCK,
        model="mock-tts-v0",
        voice_sample_sha256="sample-a",
        prompt_version="v01",
    )
    key_b = service.cache_key(
        normalized_text="你好。",
        emotion="encourage",
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        provider=TtsProviderName.MOCK,
        model="mock-tts-v0",
        voice_sample_sha256="sample-b",
        prompt_version="v01",
    )

    assert key_a != key_b


def test_tts_cache_metadata_does_not_store_raw_text(tmp_path: Path) -> None:
    service = TtsCacheService(cache_dir=tmp_path / "cache")
    cache_key = "a" * 64

    service.save(
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        cache_key=cache_key,
        audio_bytes=b"RIFF-test",
        metadata={
            "textHash": "hash-only",
            "emotion": "encourage",
            "provider": "mock",
            "model": "mock-tts-v0",
        },
    )

    metadata = service.load_metadata(
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        cache_key=cache_key,
    )

    assert metadata["textHash"] == "hash-only"
    assert "text" not in metadata
    assert service.has(
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        cache_key=cache_key,
    )
