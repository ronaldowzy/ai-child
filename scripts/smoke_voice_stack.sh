#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PORT="${VOICE_SMOKE_PORT:-18091}"
BASE_URL="${VOICE_SMOKE_BASE_URL:-http://127.0.0.1:${PORT}}"
START_SERVER="${VOICE_SMOKE_START_SERVER:-true}"
SERVER_PID=""

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi
  if command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if [[ -x "/opt/homebrew/bin/conda" ]] && /opt/homebrew/bin/conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(/opt/homebrew/bin/conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  echo "No Python interpreter found. Set PYTHON_BIN." >&2
  exit 1
}

wait_for_health() {
  local url="${BASE_URL%/}/api/v1/health"
  for _ in $(seq 1 80); do
    if curl --noproxy '*' -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Voice smoke backend did not become healthy: ${url}" >&2
  return 1
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

resolve_python_cmd

if [[ "${START_SERVER}" == "true" ]]; then
  (
    cd "${BACKEND_DIR}"
    CHILD_AI_MODEL_PROVIDER=mock \
    CHILD_AI_ASR_PROVIDER=mock \
    CHILD_AI_TTS_PROVIDER=mock \
    CHILD_AI_CONVERSATION_TTS_ENABLED=true \
    CHILD_AI_TTS_PUBLIC_BASE_URL=/media/tts \
    "${PYTHON_CMD[@]}" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" --log-level warning
  ) &
  SERVER_PID="$!"
  wait_for_health
else
  wait_for_health
fi

"${PYTHON_CMD[@]}" - "${BASE_URL}" <<'PY'
import json
import sys
import urllib.error
import urllib.request


base_url = sys.argv[1].rstrip("/")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request_json(method, path, payload=None, *, accept="application/json"):
    data = None
    headers = {"Accept": accept, "X-Request-ID": "voice-stack-smoke"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=25) as response:
            body = response.read().decode("utf-8")
            if accept == "application/x-ndjson":
                return response.status, body
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path} failed: {exc.code} {detail}") from exc


status, asr = request_json(
    "POST",
    "/api/v1/asr/transcribe",
    {
        "childId": "voice_smoke_child",
        "sessionId": "voice-smoke-session",
        "audio": {
            "data": "data:audio/wav;base64,UklGRgAAAAA=",
            "format": "wav",
            "sampleRateHz": 16000,
            "channelCount": 1,
            "durationMs": 500,
        },
        "language": "zh-CN",
        "mode": "confirm_before_send",
        "metadata": {"mock_transcript": "你好小白狐，我们来测试语音输入。"},
    },
)
assert status == 200
assert asr["status"] == "ok"
assert asr["provider"] == "mock"
assert asr["requiresConfirmation"] is True
print(f"asr_provider={asr['provider']}")

status, tts = request_json(
    "POST",
    "/api/v1/tts/xiaobaohu",
    {
        "text": "你好呀，我是小白狐。",
        "emotion": "calm",
        "voiceVersion": "xiaobaohu_v01",
        "forceRefresh": False,
    },
)
assert status == 200
assert tts["provider"] == "mock"
assert tts["audioUrl"].startswith("/media/tts/")
print(f"tts_audioUrl={tts['audioUrl']}")

status, ndjson = request_json(
    "POST",
    "/api/v1/conversation/stream",
    {
        "child_id": "voice_smoke_child",
        "session_id": "voice-smoke-stream-session",
        "input": {"type": "text", "text": "我想聊恐龙", "attachments": []},
        "client_context": {
            "device_time": "2026-05-22T16:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
        "stream_options": {
            "protocol_version": "stream.v0.1",
            "text_granularity": "sentence",
            "include_tts": True,
            "audio_delivery": "url",
            "client_turn_id": "voice_stack_smoke",
        },
    },
    accept="application/x-ndjson",
)
assert status == 200
events = [json.loads(line) for line in ndjson.splitlines() if line.strip()]
types = [event["type"] for event in events]
assert "tts_started" in types
assert "audio_ready" in types
assert types[-1] == "done"
done = events[-1]["payload"]
assert done["audio_segment_count"] >= 1
print(f"stream_audio_segment_count={done['audio_segment_count']}")
print("VOICE_STACK_SMOKE: PASS")
PY
