#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${ASR_SMOKE_BASE_URL:-http://127.0.0.1:8000}"
TMP_DIR="${TMPDIR:-/tmp}/child-ai-mimo-asr-smoke"

required_vars=(
  CHILD_AI_ASR_PROVIDER
  CHILD_AI_MIMO_ASR_ENABLED
  CHILD_AI_MIMO_ASR_API_KEY
  CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO
  CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED
  CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED
  CHILD_AI_MIMO_ASR_FAKE_AUDIO_PATH
  CHILD_AI_MIMO_ASR_FAKE_AUDIO_CONFIRMED
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required env: ${var_name}" >&2
    exit 1
  fi
done

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

if [[ "${CHILD_AI_MIMO_ASR_FAKE_AUDIO_CONFIRMED}" != "true" ]]; then
  echo "Set CHILD_AI_MIMO_ASR_FAKE_AUDIO_CONFIRMED=true after confirming the file is fake/smoke audio, not a real child recording." >&2
  exit 1
fi

fake_audio_path="${CHILD_AI_MIMO_ASR_FAKE_AUDIO_PATH}"
fake_audio_name="$(basename "${fake_audio_path}" | tr '[:upper:]' '[:lower:]')"
case "${fake_audio_name}" in
  *fake*|*smoke*|*test*|*fixture*|*sample*) ;;
  *)
    echo "Fake ASR smoke audio filename must include fake, smoke, test, fixture, or sample." >&2
    exit 1
    ;;
esac

if [[ ! -f "${fake_audio_path}" ]]; then
  echo "Missing fake ASR audio file: ${fake_audio_path}" >&2
  exit 1
fi

if [[ "${fake_audio_name}" != *.wav ]]; then
  echo "MiMo ASR smoke currently requires a .wav fake audio file." >&2
  exit 1
fi

audio_size="$(wc -c < "${fake_audio_path}" | tr -d ' ')"
if [[ "${audio_size}" -le 0 ]]; then
  echo "Fake ASR audio file is empty." >&2
  exit 1
fi
if [[ "${audio_size}" -gt 10485760 ]]; then
  echo "Fake ASR audio file exceeds the 10MB backend ASR smoke limit." >&2
  exit 1
fi

audio_sha="$(shasum -a 256 "${fake_audio_path}" | awk '{print $1}')"
mkdir -p "${TMP_DIR}"
request_file="${TMP_DIR}/request.json"
response_file="${TMP_DIR}/response.json"
trap 'rm -f "${request_file}" "${response_file}"' EXIT

python3 - "${fake_audio_path}" "${request_file}" <<'PY'
import base64
import json
import os
import sys

audio_path = sys.argv[1]
request_path = sys.argv[2]
duration_ms = int(os.environ.get("CHILD_AI_MIMO_ASR_FAKE_AUDIO_DURATION_MS", "1000"))
with open(audio_path, "rb") as audio_file:
    data_uri = "data:audio/wav;base64," + base64.b64encode(audio_file.read()).decode("ascii")

payload = {
    "childId": "asr_smoke_fake_child",
    "sessionId": "asr-smoke-session",
    "audio": {
        "data": data_uri,
        "format": "wav",
        "sampleRateHz": 16000,
        "channelCount": 1,
        "durationMs": duration_ms,
    },
    "language": "zh-CN",
    "mode": "confirm_before_send",
}
with open(request_path, "w", encoding="utf-8") as request_file:
    json.dump(payload, request_file, ensure_ascii=False)
PY

echo "fake_audio=${fake_audio_path}"
echo "fake_audio_bytes=${audio_size}"
echo "fake_audio_sha256=${audio_sha}"
echo "base_url=${BASE_URL}"
echo "asr_provider=mimo"
echo "asr_model=${CHILD_AI_MIMO_ASR_MODEL:-mimo-v2.5}"
echo "asr_api_key=set(len=${#CHILD_AI_MIMO_ASR_API_KEY})"

http_code="$(
  curl --noproxy '*' -sS -o "${response_file}" -w '%{http_code}' \
    -X POST "${BASE_URL%/}/api/v1/asr/transcribe" \
    -H 'content-type: application/json' \
    -d @"${request_file}"
)"

if [[ "${http_code}" != "200" ]]; then
  echo "ASR endpoint failed: http_status=${http_code}" >&2
  python3 - "${response_file}" <<'PY' >&2
import json
import sys

path = sys.argv[1]

def scrub(value):
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        if value.startswith("data:audio/") or len(value) > 300:
            return f"<redacted len={len(value)}>"
    return value

try:
    body = json.load(open(path, encoding="utf-8"))
except Exception:
    print("<non-json response redacted>")
else:
    print(json.dumps(scrub(body), ensure_ascii=False)[:1000])
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
requires_confirmation = body.get("requiresConfirmation")
transcript = body.get("transcript")
transcript_chars = len(transcript) if isinstance(transcript, str) else 0
error_code = body.get("errorCode") or ""
fallback_action = body.get("fallbackAction") or ""

print(f"status={status}")
print(f"provider={provider}")
print(f"model={model}")
print(f"requiresConfirmation={requires_confirmation}")
print(f"transcript_chars={transcript_chars}")
print(f"errorCode={error_code}")
print(f"fallbackAction={fallback_action}")

if provider != "mimo":
    raise SystemExit(f"Expected provider=mimo, got provider={provider}")
if requires_confirmation is not True:
    raise SystemExit("ASR response must keep requiresConfirmation=true")
if status not in {"ok", "needs_retry"}:
    raise SystemExit(f"Unexpected ASR status={status}")
PY

echo "MIMO_ASR_SMOKE: PASS"
