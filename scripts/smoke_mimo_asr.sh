#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${ASR_SMOKE_BASE_URL:-http://127.0.0.1:8000}"
TMP_DIR="${TMPDIR:-/tmp}/child-ai-mimo-asr-smoke"
converted_audio_path=""
request_file="${TMP_DIR}/request.json"
response_file="${TMP_DIR}/response.json"
trap 'rm -f "${request_file}" "${response_file}" "${converted_audio_path}"' EXIT

required_vars=(
  CHILD_AI_ASR_PROVIDER
  CHILD_AI_MIMO_ASR_ENABLED
  CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO
  CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED
  CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED
  CHILD_AI_ASR_SMOKE_WAV
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required env: ${var_name}" >&2
    exit 1
  fi
done

if [[ -z "${CHILD_AI_MIMO_ASR_API_KEY:-}" && -z "${CHILD_AI_MIMO_API_KEY:-}" && -z "${CHILD_AI_MIMO_TTS_API_KEY:-}" ]]; then
  echo "Missing MiMo API key: set CHILD_AI_MIMO_ASR_API_KEY, CHILD_AI_MIMO_API_KEY, or CHILD_AI_MIMO_TTS_API_KEY." >&2
  exit 1
fi

if [[ "${CHILD_AI_ASR_PROVIDER}" != "mimo" ]]; then
  echo "CHILD_AI_ASR_PROVIDER must be mimo for real MiMo ASR smoke." >&2
  exit 1
fi

if [[ "${CHILD_AI_MIMO_ASR_ENABLED}" != "true" ]]; then
  echo "CHILD_AI_MIMO_ASR_ENABLED must be true for real MiMo ASR smoke." >&2
  exit 1
fi

if [[ "${CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO}" != "true" ]]; then
  echo "CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO must be true for MiMo ASR smoke." >&2
  exit 1
fi

if [[ "${CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED}" != "true" ]]; then
  echo "CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED must be true." >&2
  exit 1
fi

if [[ "${CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED}" != "true" ]]; then
  echo "CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED must be true." >&2
  exit 1
fi

smoke_audio_path="${CHILD_AI_ASR_SMOKE_WAV}"
smoke_audio_name="$(basename "${smoke_audio_path}" | tr '[:upper:]' '[:lower:]')"
case "${smoke_audio_name}" in
  *fake*|*smoke*|*test*|*fixture*|*sample*) ;;
  *)
    echo "ASR smoke audio filename must include fake, smoke, test, fixture, or sample." >&2
    exit 1
    ;;
esac

if [[ ! -f "${smoke_audio_path}" ]]; then
  echo "Missing ASR smoke audio file." >&2
  exit 1
fi

mkdir -p "${TMP_DIR}"

case "${smoke_audio_name}" in
  *.wav) audio_format="wav" ;;
  *.m4a) audio_format="m4a" ;;
  *)
    echo "MiMo ASR smoke currently supports .wav or .m4a smoke audio." >&2
    exit 1
    ;;
esac

audio_size="$(wc -c < "${smoke_audio_path}" | tr -d ' ')"
if [[ "${audio_size}" -le 0 ]]; then
  echo "ASR smoke audio file is empty." >&2
  exit 1
fi
if [[ "${audio_size}" -gt 10485760 ]]; then
  echo "ASR smoke audio file exceeds the 10MB backend ASR smoke limit." >&2
  exit 1
fi

if [[ "${audio_format}" == "m4a" ]]; then
  converted_audio_path="${TMP_DIR}/asr-smoke-converted.wav"
  if command -v afconvert >/dev/null 2>&1; then
    afconvert -f WAVE -d LEI16@16000 -c 1 \
      "${smoke_audio_path}" "${converted_audio_path}" >/dev/null
  elif command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -y -loglevel error -i "${smoke_audio_path}" \
      -ac 1 -ar 16000 -sample_fmt s16 "${converted_audio_path}" >/dev/null
  else
    echo "M4A smoke audio must be converted to 16k mono WAV first; install ffmpeg or run on macOS with afconvert." >&2
    exit 1
  fi
  smoke_audio_path="${converted_audio_path}"
  audio_format="wav"
  audio_size="$(wc -c < "${smoke_audio_path}" | tr -d ' ')"
  if [[ "${audio_size}" -gt 10485760 ]]; then
    echo "Converted ASR smoke WAV exceeds the 10MB backend ASR smoke limit." >&2
    exit 1
  fi
fi

duration_ms="${CHILD_AI_ASR_SMOKE_DURATION_MS:-${CHILD_AI_MIMO_ASR_FAKE_AUDIO_DURATION_MS:-1000}}"
if ! [[ "${duration_ms}" =~ ^[0-9]+$ ]]; then
  echo "CHILD_AI_ASR_SMOKE_DURATION_MS must be a positive integer when set." >&2
  exit 1
fi
if [[ "${duration_ms}" -le 0 || "${duration_ms}" -gt 30000 ]]; then
  echo "CHILD_AI_ASR_SMOKE_DURATION_MS must be between 1 and 30000." >&2
  exit 1
fi

python3 - "${smoke_audio_path}" "${request_file}" "${audio_format}" "${duration_ms}" <<'PY'
import base64
import json
import sys

audio_path = sys.argv[1]
request_path = sys.argv[2]
audio_format = sys.argv[3]
duration_ms = int(sys.argv[4])
with open(audio_path, "rb") as audio_file:
    data_uri = (
        f"data:audio/{audio_format};base64,"
        + base64.b64encode(audio_file.read()).decode("ascii")
    )

payload = {
    "childId": "asr_smoke_child",
    "sessionId": "asr-smoke-session",
    "audio": {
        "data": data_uri,
        "format": audio_format,
        "durationMs": duration_ms,
    },
    "language": "zh-CN",
    "mode": "confirm_before_send",
}
if audio_format == "wav":
    payload["audio"]["sampleRateHz"] = 16000
    payload["audio"]["channelCount"] = 1
with open(request_path, "w", encoding="utf-8") as request_file:
    json.dump(payload, request_file, ensure_ascii=False)
PY

http_code="$(
  curl --noproxy '*' -sS -o "${response_file}" -w '%{http_code}' \
    -X POST "${BASE_URL%/}/api/v1/asr/transcribe" \
    -H 'content-type: application/json' \
    -d @"${request_file}" 2>/dev/null || true
)"
if [[ -z "${http_code}" ]]; then
  http_code="000"
fi

if [[ "${http_code}" != "200" ]]; then
  python3 - "${response_file}" "${http_code}" <<'PY'
import json
import sys

path = sys.argv[1]
http_code = sys.argv[2]
try:
    body = json.load(open(path, encoding="utf-8"))
except Exception:
    body = {}

def field(value):
    return "" if value is None else value

print(f"status={body.get('status') or 'failed'}")
print(f"provider={body.get('provider') or ''}")
print(f"model={body.get('model') or ''}")
print(f"duration={field(body.get('durationMs'))}")
print(f"confidence={field(body.get('confidence'))}")
print(f"errorCode={body.get('errorCode') or 'http_' + http_code}")
PY
  exit 1
fi

python3 - "${response_file}" <<'PY'
import json
import sys

body = json.load(open(sys.argv[1], encoding="utf-8"))
status = body.get("status", "")
provider = body.get("provider", "")
model = body.get("model", "")
duration = body.get("durationMs")
confidence = body.get("confidence")
requires_confirmation = body.get("requiresConfirmation")
error_code = body.get("errorCode") or ""

def field(value):
    return "" if value is None else value

print(f"status={status}")
print(f"provider={provider}")
print(f"model={model}")
print(f"duration={field(duration)}")
print(f"confidence={field(confidence)}")
print(f"errorCode={error_code}")

if provider != "mimo":
    raise SystemExit(f"Expected provider=mimo, got provider={provider}")
if requires_confirmation is not True:
    raise SystemExit("ASR response must keep requiresConfirmation=true")
if status not in {"ok", "needs_retry"}:
    raise SystemExit(f"Unexpected ASR status={status}")
PY
