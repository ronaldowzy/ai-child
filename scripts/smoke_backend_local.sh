#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PORT="${BACKEND_SMOKE_PORT:-18090}"
BASE_URL="${BACKEND_SMOKE_BASE_URL:-http://127.0.0.1:${PORT}}"
START_SERVER="${BACKEND_SMOKE_START_SERVER:-true}"
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
  echo "Backend smoke server did not become healthy: ${url}" >&2
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
    CHILD_AI_CONVERSATION_TTS_ENABLED=false \
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
child_id = "child_smoke_backend_local"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request_json(method, path, payload=None, *, accept="application/json"):
    data = None
    headers = {"Accept": accept, "X-Request-ID": "backend-local-smoke"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            if accept == "application/x-ndjson":
                return response.status, body
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path} failed: {exc.code} {detail}") from exc


def conversation_payload(session_id, text, *, include_stream_options=False):
    payload = {
        "child_id": child_id,
        "session_id": session_id,
        "input": {"type": "text", "text": text, "attachments": []},
        "client_context": {
            "device_time": "2026-05-22T16:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }
    if include_stream_options:
        payload["stream_options"] = {
            "protocol_version": "stream.v0.1",
            "text_granularity": "sentence",
            "include_tts": False,
            "audio_delivery": "url",
            "client_turn_id": "backend_local_smoke",
        }
    return payload


status, health = request_json("GET", "/api/v1/health/detail")
assert status == 200
assert health.get("status") in {"ok", "degraded"}
print(f"health_detail={health.get('status')}")

status, message = request_json(
    "POST",
    "/api/v1/conversation/message",
    conversation_payload("smoke_message_session", "我有一道题不会"),
)
assert status == 200
assert message["reply"]["text"]
assert message["session_state"]["active_scene"] == "learning.homework_help"
print(f"message_scene={message['session_state']['active_scene']}")

status, ndjson = request_json(
    "POST",
    "/api/v1/conversation/stream",
    conversation_payload("smoke_stream_session", "我想聊恐龙", include_stream_options=True),
    accept="application/x-ndjson",
)
assert status == 200
events = [json.loads(line) for line in ndjson.splitlines() if line.strip()]
types = [event["type"] for event in events]
assert types[0] == "session_started"
assert "route_decision" in types
assert "text_delta" in types
assert types[-1] == "done"
print(f"stream_events={','.join(types)}")

status, policy = request_json(
    "POST",
    "/api/v1/parent/policy",
    {
        "child_id": child_id,
        "child_nickname": "豆豆",
        "parent_message_raw": "最近用轻松问题陪孩子聊，不要查岗。",
        "goals": ["先听孩子说，再给小步骤"],
    },
)
assert status == 200
assert policy["child_nickname"] == "豆豆"
status, policy_read = request_json("GET", f"/api/v1/parent/policy/{child_id}")
assert status == 200
assert policy_read["child_nickname"] == "豆豆"
print("parent_policy=ok")

status, report = request_json("GET", f"/api/v1/parent/reports/{child_id}")
assert status == 200
assert report["child_id"] == child_id
assert "evidence" not in json.dumps(report, ensure_ascii=False)
print(f"parent_report_date={report['date']}")
print("BACKEND_LOCAL_SMOKE: PASS")
PY
