#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${TTS_SMOKE_BASE_URL:-http://127.0.0.1:8000}"
VOICE_SAMPLE="${ROOT_DIR}/backend/assets/voices/xiaobaohu_voice_v01.wav"
TMP_DIR="${TMPDIR:-/tmp}/child-ai-mimo-tts-smoke"
TEXT="你好呀，我是小白狐。我们先慢慢说，一次说一件事就好。"

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "Missing local .env. Add MiMo credentials locally; never commit .env." >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"
set +a

export CHILD_AI_TTS_PROVIDER="${CHILD_AI_TTS_PROVIDER:-mimo}"
export CHILD_AI_CONVERSATION_TTS_ENABLED="${CHILD_AI_CONVERSATION_TTS_ENABLED:-true}"
export CHILD_AI_MIMO_TTS_ENABLED="${CHILD_AI_MIMO_TTS_ENABLED:-true}"
export CHILD_AI_MIMO_TTS_API_KEY="${CHILD_AI_MIMO_TTS_API_KEY:-${CHILD_AI_MIMO_API_KEY:-}}"
export CHILD_AI_MIMO_TTS_BASE_URL="${CHILD_AI_MIMO_TTS_BASE_URL:-https://token-plan-cn.xiaomimimo.com/v1}"
export CHILD_AI_MIMO_TTS_MODEL="${CHILD_AI_MIMO_TTS_MODEL:-mimo-v2.5-tts-voiceclone}"
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT="${CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT:-true}"
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED="${CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED:-true}"
export CHILD_AI_XIAOBAIHU_VOICE_SAMPLE_PATH="${CHILD_AI_XIAOBAIHU_VOICE_SAMPLE_PATH:-backend/assets/voices/xiaobaohu_voice_v01.wav}"
export CHILD_AI_TTS_CACHE_DIR="${CHILD_AI_TTS_CACHE_DIR:-backend/storage/tts_cache}"
export CHILD_AI_TTS_PUBLIC_BASE_URL="${CHILD_AI_TTS_PUBLIC_BASE_URL:-/media/tts}"
export CHILD_AI_TTS_MAX_TEXT_CHARS="${CHILD_AI_TTS_MAX_TEXT_CHARS:-300}"

required_vars=(
  CHILD_AI_TTS_PROVIDER
  CHILD_AI_CONVERSATION_TTS_ENABLED
  CHILD_AI_MIMO_TTS_ENABLED
  CHILD_AI_MIMO_TTS_API_KEY
  CHILD_AI_MIMO_TTS_BASE_URL
  CHILD_AI_MIMO_TTS_MODEL
  CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT
  CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED
  CHILD_AI_XIAOBAIHU_VOICE_SAMPLE_PATH
  CHILD_AI_TTS_CACHE_DIR
  CHILD_AI_TTS_PUBLIC_BASE_URL
  CHILD_AI_TTS_MAX_TEXT_CHARS
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required env: ${var_name}" >&2
    exit 1
  fi
done

if [[ "${CHILD_AI_TTS_PROVIDER}" != "mimo" ]]; then
  echo "CHILD_AI_TTS_PROVIDER must be mimo for real TTS smoke." >&2
  exit 1
fi

if [[ "${CHILD_AI_MIMO_TTS_ENABLED}" != "true" ]]; then
  echo "CHILD_AI_MIMO_TTS_ENABLED must be true for real TTS smoke." >&2
  exit 1
fi

if [[ ! -f "${VOICE_SAMPLE}" ]]; then
  echo "Missing voice sample: ${VOICE_SAMPLE}" >&2
  exit 1
fi

voice_size="$(wc -c < "${VOICE_SAMPLE}" | tr -d ' ')"
if [[ "${voice_size}" -le 1024 ]]; then
  echo "Voice sample is too small: ${voice_size} bytes" >&2
  exit 1
fi

voice_sha="$(shasum -a 256 "${VOICE_SAMPLE}" | awk '{print $1}')"
mkdir -p "${TMP_DIR}"

echo "voice_sample=${VOICE_SAMPLE}"
echo "voice_sample_bytes=${voice_size}"
echo "voice_sample_sha256=${voice_sha}"
echo "base_url=${BASE_URL}"
echo "tts_provider=mimo"
echo "tts_model=${CHILD_AI_MIMO_TTS_MODEL}"
echo "tts_api_key=set(len=${#CHILD_AI_MIMO_TTS_API_KEY})"

response_file="${TMP_DIR}/response.json"
http_code="$(
  curl --noproxy '*' -sS -o "${response_file}" -w '%{http_code}' \
    -X POST "${BASE_URL%/}/api/v1/tts/xiaobaohu" \
    -H 'content-type: application/json' \
    -d "{\"text\":\"${TEXT}\",\"emotion\":\"encourage\",\"voiceVersion\":\"xiaobaohu_v01\",\"forceRefresh\":true}"
)"

if [[ "${http_code}" != "200" ]]; then
  echo "TTS endpoint failed: http_status=${http_code}" >&2
  python3 - "${response_file}" <<'PY' >&2
import json
import sys
path = sys.argv[1]
try:
    body = json.load(open(path, encoding="utf-8"))
except Exception:
    print(open(path, encoding="utf-8", errors="replace").read()[:1000])
else:
    print(json.dumps(body, ensure_ascii=False)[:1000])
PY
  exit 1
fi

read -r provider model cache_hit audio_url duration < <(
  python3 - "${response_file}" <<'PY'
import json
import sys
body = json.load(open(sys.argv[1], encoding="utf-8"))
print(
    body.get("provider", ""),
    body.get("model", ""),
    str(body.get("cacheHit", "")),
    body.get("audioUrl", ""),
    str(body.get("duration", "")),
)
PY
)

echo "provider=${provider}"
echo "model=${model}"
echo "cacheHit=${cache_hit}"
echo "audioUrl=${audio_url}"
echo "duration=${duration}"

if [[ "${provider}" != "mimo" ]]; then
  echo "Expected provider=mimo, got provider=${provider}" >&2
  exit 1
fi

if [[ "${audio_url}" != /media/tts/* ]]; then
  echo "Unexpected audioUrl: ${audio_url}" >&2
  exit 1
fi

audio_file="${TMP_DIR}/xiaobaohu_mimo_tts.wav"
curl --noproxy '*' -sS -f "${BASE_URL%/}${audio_url}" -o "${audio_file}"
audio_size="$(wc -c < "${audio_file}" | tr -d ' ')"
if [[ "${audio_size}" -le 1024 ]]; then
  echo "Downloaded audio is too small: ${audio_size} bytes" >&2
  exit 1
fi

if ! head -c 4 "${audio_file}" | grep -q "RIFF"; then
  echo "Downloaded audio is not a RIFF/WAV file: ${audio_file}" >&2
  exit 1
fi

audio_sha="$(shasum -a 256 "${audio_file}" | awk '{print $1}')"
echo "downloaded_audio=${audio_file}"
echo "downloaded_audio_bytes=${audio_size}"
echo "downloaded_audio_sha256=${audio_sha}"

if [[ "${TTS_SMOKE_SKIP_CONVERSATION:-false}" != "true" ]]; then
  conversation_response_file="${TMP_DIR}/conversation_response.json"
  conversation_audio_file="${TMP_DIR}/conversation_xiaobaohu_mimo_tts.wav"
  conversation_http_code="$(
    curl --noproxy '*' -sS -o "${conversation_response_file}" -w '%{http_code}' \
      -X POST "${BASE_URL%/}/api/v1/conversation/message" \
      -H 'content-type: application/json' \
      -d '{
        "child_id": "local_child_001",
        "session_id": "tts-smoke-session",
        "input": {
          "type": "text",
          "text": "你好小白狐，我们聊一会儿吧",
          "attachments": []
        },
        "client_context": {
          "device_time": "2026-05-20T18:30:00+08:00",
          "timezone": "Asia/Shanghai",
          "app_mode": "child"
        }
      }'
  )"

  if [[ "${conversation_http_code}" != "200" ]]; then
    echo "Conversation TTS smoke failed: http_status=${conversation_http_code}" >&2
    python3 - "${conversation_response_file}" <<'PY' >&2
import json
import sys
path = sys.argv[1]
try:
    body = json.load(open(path, encoding="utf-8"))
except Exception:
    print(open(path, encoding="utf-8", errors="replace").read()[:1000])
else:
    print(json.dumps(body, ensure_ascii=False)[:1000])
PY
    exit 1
  fi

  read -r reply_present voice_enabled conversation_audio_url < <(
    python3 - "${conversation_response_file}" <<'PY'
import json
import sys
body = json.load(open(sys.argv[1], encoding="utf-8"))
reply = body.get("reply", {})
print(
    str(bool(reply.get("text"))),
    str(reply.get("voice_enabled")),
    reply.get("audio_url") or "",
)
PY
  )

  echo "conversation_reply_text_present=${reply_present}"
  echo "conversation_voice_enabled=${voice_enabled}"
  echo "conversation_audioUrl=${conversation_audio_url}"

  if [[ "${reply_present}" != "True" ]]; then
    echo "Conversation response has no reply.text" >&2
    exit 1
  fi

  if [[ "${conversation_audio_url}" != /media/tts/* ]]; then
    echo "Conversation response has unexpected audioUrl: ${conversation_audio_url}" >&2
    exit 1
  fi

  curl --noproxy '*' -sS -f "${BASE_URL%/}${conversation_audio_url}" \
    -o "${conversation_audio_file}"
  conversation_audio_size="$(wc -c < "${conversation_audio_file}" | tr -d ' ')"
  if [[ "${conversation_audio_size}" -le 1024 ]]; then
    echo "Conversation audio is too small: ${conversation_audio_size} bytes" >&2
    exit 1
  fi
  if ! head -c 4 "${conversation_audio_file}" | grep -q "RIFF"; then
    echo "Conversation audio is not a RIFF/WAV file: ${conversation_audio_file}" >&2
    exit 1
  fi
  conversation_audio_sha="$(shasum -a 256 "${conversation_audio_file}" | awk '{print $1}')"
  echo "conversation_downloaded_audio=${conversation_audio_file}"
  echo "conversation_downloaded_audio_bytes=${conversation_audio_size}"
  echo "conversation_downloaded_audio_sha256=${conversation_audio_sha}"
fi

echo "MIMO_TTS_SMOKE: PASS"
