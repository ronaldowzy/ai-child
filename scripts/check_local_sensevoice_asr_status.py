#!/usr/bin/env python3
"""Check local SenseVoice ASR readiness without using child audio.

This is a dev/QA smoke harness. It sets a process-local ASR env overlay,
optionally generates a silent WAV, calls the backend AsrService, and writes a
small Markdown report. It must not persist audio, base64 payloads, raw provider
responses, or secrets.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "LOCAL_ASR_SENSEVOICE_SMOKE_V0_1.md"
DEFAULT_MODEL_PATH = REPO_ROOT / "backend/models/asr/sensevoice/model.int8.onnx"
DEFAULT_TOKENS_PATH = REPO_ROOT / "backend/models/asr/sensevoice/tokens.txt"
SILENT_WAV_NAME = "child-ai-local-sensevoice-silent-smoke.wav"

STATUS_PASS = "PASS"
STATUS_BLOCKED = "BLOCKED"
STATUS_FAIL = "FAIL"


@dataclass(frozen=True)
class DependencyCheck:
    numpy_present: bool
    sherpa_onnx_present: bool

    @property
    def missing_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.numpy_present:
            reasons.append("missing_numpy_dependency")
        if not self.sherpa_onnx_present:
            reasons.append("missing_sherpa_onnx_dependency")
        return tuple(reasons)


@dataclass(frozen=True)
class ModelFileCheck:
    model_path: Path
    tokens_path: Path
    model_present: bool
    tokens_present: bool

    @property
    def missing_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.model_present:
            reasons.append("missing_local_sensevoice_model")
        if not self.tokens_present:
            reasons.append("missing_local_sensevoice_tokens")
        return tuple(reasons)


@dataclass
class LocalSenseVoiceSmokeResult:
    status: str
    reason: str | None
    commit: str
    dependency_check: DependencyCheck
    model_check: ModelFileCheck
    audio_source: str
    audio_path: str | None
    fallback: str
    provider: str | None = None
    model: str | None = None
    transcript_status: str | None = None
    transcript_chars: int | None = None
    confidence: float | None = None
    duration_ms: int | None = None
    elapsed_ms: float | None = None
    local_primary_failed: bool = False
    fallback_used: bool = False
    error_code: str | None = None
    error_type: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


def _ensure_backend_imports() -> None:
    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _dependency_check() -> DependencyCheck:
    return DependencyCheck(
        numpy_present=importlib.util.find_spec("numpy") is not None,
        sherpa_onnx_present=importlib.util.find_spec("sherpa_onnx") is not None,
    )


def _model_file_check(model_path: Path, tokens_path: Path) -> ModelFileCheck:
    return ModelFileCheck(
        model_path=model_path,
        tokens_path=tokens_path,
        model_present=model_path.is_file(),
        tokens_present=tokens_path.is_file(),
    )


def _generate_silent_wav() -> Path:
    output_path = Path(tempfile.gettempdir()) / SILENT_WAV_NAME
    sample_rate = 16_000
    duration_seconds = 1
    frames = b"\x00\x00" * sample_rate * duration_seconds
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)
    return output_path


def _audio_data_uri(audio_path: Path) -> str:
    encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    # Keep the data URI in memory only. Reports never include this value.
    return "data:" + "audio/wav;" + "base64," + encoded


def _duration_ms(audio_path: Path) -> int | None:
    try:
        with wave.open(str(audio_path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
        if rate <= 0:
            return None
        return round(frames / rate * 1000)
    except wave.Error:
        return None


def _apply_env_overlay(
    *,
    fallback: str,
    model_path: Path,
    tokens_path: Path,
) -> None:
    os.environ["CHILD_AI_ASR_PROVIDER"] = "local_sensevoice"
    os.environ["CHILD_AI_LOCAL_SENSEVOICE_ENABLED"] = "true"
    os.environ["CHILD_AI_ASR_FALLBACK_PROVIDER"] = "" if fallback == "none" else fallback
    os.environ["CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH"] = str(model_path)
    os.environ["CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH"] = str(tokens_path)
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def _transcribe(
    *,
    audio_path: Path,
    fallback: str,
    model_path: Path,
    tokens_path: Path,
) -> object:
    _ensure_backend_imports()
    from app.domain.schemas.asr import AsrTranscriptionRequest
    from app.core.config import get_settings
    from app.services.asr_service import AsrService

    env_keys = (
        "CHILD_AI_ASR_PROVIDER",
        "CHILD_AI_LOCAL_SENSEVOICE_ENABLED",
        "CHILD_AI_ASR_FALLBACK_PROVIDER",
        "CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH",
        "CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH",
    )
    previous_env = {key: os.environ.get(key) for key in env_keys}

    request = AsrTranscriptionRequest.model_validate(
        {
            "childId": "local_sensevoice_smoke_child",
            "sessionId": "local_sensevoice_smoke_session",
            "audio": {
                "data": _audio_data_uri(audio_path),
                "format": "wav",
                "sampleRateHz": 16000,
                "channelCount": 1,
                "durationMs": _duration_ms(audio_path) or 1000,
            },
            "language": "zh-CN",
            "mode": "confirm_before_send",
            "metadata": {
                # Used only if the local primary fails and fallback=mock.
                "mock_transcript": "本地语音识别烟测",
            },
        }
    )
    try:
        _apply_env_overlay(
            fallback=fallback,
            model_path=model_path,
            tokens_path=tokens_path,
        )
        return AsrService().transcribe(request)
    finally:
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def run_smoke(
    *,
    audio: Path | None = None,
    fallback: str = "mock",
    expect_pass: bool = False,
    output: Path = DEFAULT_REPORT_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
    tokens_path: Path = DEFAULT_TOKENS_PATH,
) -> LocalSenseVoiceSmokeResult:
    started_at = time.perf_counter()
    dependency_check = _dependency_check()
    model_check = _model_file_check(model_path, tokens_path)
    notes: list[str] = []
    audio_source = "none"
    audio_path: Path | None = None

    if audio is None:
        if expect_pass:
            result = LocalSenseVoiceSmokeResult(
                status=STATUS_BLOCKED,
                reason="missing_audio_path_when_expect_pass",
                commit=_commit_hash(),
                dependency_check=dependency_check,
                model_check=model_check,
                audio_source=audio_source,
                audio_path=None,
                fallback=fallback,
                elapsed_ms=round((time.perf_counter() - started_at) * 1000, 1),
                notes=("No non-child WAV was provided while --expect-pass was set.",),
            )
            write_report(result, output)
            return result
        audio_path = _generate_silent_wav()
        audio_source = "silent_generated"
        notes.append(
            "Generated 1s silent WAV; this verifies provider/init behavior only, "
            "not Chinese recognition accuracy."
        )
    else:
        audio_path = audio
        audio_source = "user_non_child_wav"

    block_reasons = list(dependency_check.missing_reasons)
    block_reasons.extend(model_check.missing_reasons)
    if audio_path and not audio_path.is_file():
        block_reasons.append("missing_audio_file")

    response: object | None = None
    call_error_type: str | None = None
    call_error_code: str | None = None
    if audio_path and audio_path.is_file():
        try:
            response = _transcribe(
                audio_path=audio_path,
                fallback=fallback,
                model_path=model_path,
                tokens_path=tokens_path,
            )
        except Exception as exc:
            call_error_type = exc.__class__.__name__
            call_error_code = str(exc).splitlines()[0][:160] if str(exc) else None

    provider = getattr(response, "provider", None)
    provider_value = getattr(provider, "value", provider) if provider is not None else None
    transcript = getattr(response, "transcript", None)
    transcript_chars = len(transcript) if isinstance(transcript, str) else 0
    transcript_status = getattr(getattr(response, "status", None), "value", None)
    if transcript_status is None:
        transcript_status = getattr(response, "status", None)

    fallback_used = provider_value is not None and provider_value != "local_sensevoice"
    local_primary_failed = bool(block_reasons or fallback_used or call_error_type)

    if provider_value == "local_sensevoice" and transcript_status in {"ok", "needs_retry"}:
        status = STATUS_PASS
        reason = None
    elif fallback_used and provider_value == "mock":
        status = STATUS_BLOCKED
        reason = "local_primary_failed_fallback_mock"
    elif fallback_used and provider_value == "mimo":
        status = STATUS_BLOCKED
        reason = "local_primary_failed_fallback_mimo"
    elif block_reasons:
        status = STATUS_BLOCKED
        reason = ",".join(block_reasons)
    elif call_error_type:
        status = STATUS_FAIL
        reason = call_error_type
    else:
        status = STATUS_FAIL
        reason = "unknown_local_sensevoice_smoke_failure"

    result = LocalSenseVoiceSmokeResult(
        status=status,
        reason=reason,
        commit=_commit_hash(),
        dependency_check=dependency_check,
        model_check=model_check,
        audio_source=audio_source,
        audio_path=str(audio_path) if audio_path else None,
        fallback=fallback,
        provider=provider_value,
        model=getattr(response, "model", None),
        transcript_status=transcript_status,
        transcript_chars=transcript_chars,
        confidence=getattr(response, "confidence", None),
        duration_ms=getattr(response, "duration_ms", None),
        elapsed_ms=round((time.perf_counter() - started_at) * 1000, 1),
        local_primary_failed=local_primary_failed,
        fallback_used=fallback_used,
        error_code=getattr(response, "error_code", None) or call_error_code,
        error_type=call_error_type,
        notes=tuple(notes),
    )
    write_report(result, output)
    return result


def write_report(result: LocalSenseVoiceSmokeResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Local SenseVoice ASR Smoke V0.1",
        "",
        "> Local ASR smoke summary. This is not real child accuracy validation, "
        "not Android device QA, and not a production data policy.",
        "",
        "## Run Metadata",
        "",
        f"- Executed at: `{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}`",
        f"- Commit: `{result.commit}`",
        f"- Status: `{result.status}`",
        f"- Reason: `{result.reason or 'none'}`",
        "- Provider under test: `local_sensevoice`",
        f"- Fallback provider: `{result.fallback}`",
        f"- Elapsed ms: `{result.elapsed_ms}`",
        "",
        "## Environment Checks",
        "",
        f"- numpy import: `{'present' if result.dependency_check.numpy_present else 'missing'}`",
        f"- sherpa_onnx import: `{'present' if result.dependency_check.sherpa_onnx_present else 'missing'}`",
        f"- model.int8.onnx: `{'present' if result.model_check.model_present else 'missing'}`",
        f"- tokens.txt: `{'present' if result.model_check.tokens_present else 'missing'}`",
        f"- model path: `{_safe_path(result.model_check.model_path)}`",
        f"- tokens path: `{_safe_path(result.model_check.tokens_path)}`",
        "",
        "## Audio Boundary",
        "",
        f"- audio source: `{result.audio_source}`",
        f"- audio path: `{_safe_audio_path(result.audio_path)}`",
        "- audio file committed: `no`",
        "- raw audio/base64 in report: `no`",
        "- real child audio used: `no`",
        "",
        "## Provider Result",
        "",
        f"- provider result: `{result.provider or 'none'}`",
        f"- model: `{result.model or 'none'}`",
        f"- transcript status: `{result.transcript_status or 'none'}`",
        f"- transcript chars: `{result.transcript_chars if result.transcript_chars is not None else 'none'}`",
        f"- confidence: `{result.confidence if result.confidence is not None else 'none'}`",
        f"- duration ms: `{result.duration_ms if result.duration_ms is not None else 'none'}`",
        f"- fallback used: `{'true' if result.fallback_used else 'false'}`",
        f"- local primary failed: `{'true' if result.local_primary_failed else 'false'}`",
        f"- error type: `{result.error_type or 'none'}`",
        f"- error code: `{result.error_code or 'none'}`",
        "",
        "## Notes",
        "",
    ]
    if result.notes:
        lines.extend(f"- {note}" for note in result.notes)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `PASS` means local dependencies and model files were present and "
            "the response provider was `local_sensevoice` with a stable API status.",
            "- `BLOCKED` means the local primary path could not be verified, or "
            "only a fallback provider responded.",
            "- `FAIL` means an unexpected provider/API failure occurred.",
            "- A silent generated WAV only verifies the request/init path; it does "
            "not validate Chinese recognition accuracy.",
            "- Real child speech accuracy and Redmi K60 / Honor Pad 5 Android QA "
            "remain separate manual validation items.",
        ]
    )
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _safe_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def _safe_audio_path(path: str | None) -> str:
    if not path:
        return "none"
    candidate = Path(path)
    if candidate.name == SILENT_WAV_NAME:
        return f"/tmp/{candidate.name}"
    return candidate.name


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check local SenseVoice ASR status with non-child smoke audio.",
    )
    parser.add_argument("--audio", type=Path, default=None, help="Non-child WAV path.")
    parser.add_argument(
        "--fallback",
        choices=("mock", "mimo", "none"),
        default="mock",
        help="Fallback provider to configure for the smoke process.",
    )
    parser.add_argument(
        "--expect-pass",
        action="store_true",
        help="Require an explicit non-child audio path for a PASS-oriented smoke.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Markdown report output path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_smoke(
        audio=args.audio,
        fallback=args.fallback,
        expect_pass=args.expect_pass,
        output=args.output,
    )
    print(f"LOCAL_SENSEVOICE_ASR_SMOKE: {result.status}")
    if result.reason:
        print(f"reason={result.reason}")
    print(f"provider={result.provider or 'none'}")
    print(f"model={result.model or 'none'}")
    print(f"fallback_used={'true' if result.fallback_used else 'false'}")
    print(f"report={args.output}")
    if result.status == STATUS_PASS:
        return 0
    if result.status == STATUS_BLOCKED:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
