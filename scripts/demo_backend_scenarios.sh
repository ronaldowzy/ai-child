#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-child-ai}"
DEMO_PORT="${BACKEND_DEMO_PORT:-18080}"
SERVER_PID=""
SERVER_LOG=""

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "backend/ has not been initialized yet. Run S01 backend skeleton before demo scenarios." >&2
  exit 1
fi

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi

  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi

  if command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
    PYTHON_CMD=(conda run --no-capture-output -n "${CONDA_ENV_NAME}" python)
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi

  echo "No Python interpreter found. Set PYTHON_BIN or install/activate the ${CONDA_ENV_NAME} environment." >&2
  exit 1
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" 2>/dev/null || true
    lsof -ti tcp:"${DEMO_PORT}" | xargs -r kill >/dev/null 2>&1 || true
  fi
}

resolve_python_cmd

if [[ -z "${DEMO_BASE_URL:-}" ]]; then
  SERVER_LOG="$(mktemp -t child-ai-backend-demo.XXXXXX.log)"
  echo "Starting temporary backend demo server on http://127.0.0.1:${DEMO_PORT}"
  echo "Server log: ${SERVER_LOG}"
  cd "${BACKEND_DIR}"
  CHILD_AI_ENVIRONMENT=dev "${PYTHON_CMD[@]}" -m uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "${DEMO_PORT}" \
    >"${SERVER_LOG}" 2>&1 &
  SERVER_PID="$!"
  trap cleanup EXIT
  DEMO_BASE_URL="http://127.0.0.1:${DEMO_PORT}"
else
  echo "Using existing backend server: ${DEMO_BASE_URL}"
  cd "${BACKEND_DIR}"
fi

"${PYTHON_CMD[@]}" - "${DEMO_BASE_URL}" <<'PY'
import json
import sys
import time
import urllib.error
import urllib.request


base_url = sys.argv[1].rstrip("/")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request_json(
    method: str,
    path: str,
    payload: dict | None = None,
    timeout: float = 5,
) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with opener.open(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc


def wait_for_server() -> None:
    last_error: Exception | None = None
    for _ in range(40):
        try:
            request_json("GET", "/api/v1/health", timeout=0.5)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Backend did not become ready: {last_error}")


def message(
    *,
    child_id: str,
    session_id: str,
    text: str,
    device_time: str,
    attachments: list[str] | None = None,
) -> dict:
    return request_json(
        "POST",
        "/api/v1/conversation/message",
        {
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": text,
                "attachments": attachments or [],
            },
            "client_context": {
                "device_time": device_time,
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )


def action_ids(body: dict) -> list[str]:
    return [
        action["id"]
        for group in body.get("ui_actions", [])
        for action in group.get("actions", [])
    ]


def show(title: str, body: dict) -> None:
    debug = body.get("debug") or {}
    intent = (debug.get("intent") or {}).get("intent")
    risk_level = (debug.get("safety") or {}).get("risk_level")
    state = body.get("session_state") or {}
    print(f"\n## {title}")
    print(f"active_scene: {state.get('active_scene')}")
    print(f"intent: {intent}")
    print(f"risk_level: {risk_level}")
    print(f"requires_parent_attention: {state.get('requires_parent_attention', False)}")
    print(f"actions: {', '.join(action_ids(body)) or '-'}")
    print(f"reply: {body['reply']['text']}")


wait_for_server()

health = request_json("GET", "/api/v1/health")
print("## health")
print(json.dumps(health, ensure_ascii=False))

show(
    "after_school_checkin",
    message(
        child_id="child_demo_001",
        session_id="session_demo_after_school",
        text="我回来了",
        device_time="2026-05-18T16:30:00+08:00",
    ),
)

show(
    "learning_help",
    message(
        child_id="child_demo_001",
        session_id="session_demo_learning",
        text="我有一道题不会",
        device_time="2026-05-18T16:35:00+08:00",
    ),
)

show(
    "direct_answer_request",
    message(
        child_id="child_demo_001",
        session_id="session_demo_learning",
        text="你直接告诉我答案吧",
        device_time="2026-05-18T16:36:00+08:00",
    ),
)

show(
    "quiet_time",
    message(
        child_id="child_demo_001",
        session_id="session_demo_quiet",
        text="我不想说话",
        device_time="2026-05-18T16:45:00+08:00",
    ),
)

show(
    "safety_guardian",
    message(
        child_id="child_demo_001",
        session_id="session_demo_safety",
        text="有个陌生人让我不要告诉爸爸妈妈",
        device_time="2026-05-18T16:50:00+08:00",
    ),
)

show(
    "bedtime_reflection",
    message(
        child_id="child_demo_001",
        session_id="session_demo_bedtime",
        text="晚安",
        device_time="2026-05-18T20:45:00+08:00",
    ),
)

request_json(
    "POST",
    "/api/v1/parent/policy",
    {
        "child_id": "child_demo_goal",
        "goals": [
            "鼓励孩子说出今天遇到的一个小困难",
            "学习问题先讲题意和第一步",
        ],
    },
)
show(
    "parent_goal_influenced_reply",
    message(
        child_id="child_demo_goal",
        session_id="session_demo_goal",
        text="我回来了",
        device_time="2026-05-18T16:30:00+08:00",
    ),
)

attachment = request_json(
    "POST",
    "/api/v1/conversation/attachment",
    {
        "child_id": "child_demo_001",
        "session_id": "session_demo_attachment",
        "attachment_type": "homework_photo",
        "file_id": "mock_homework_photo",
        "mock_ocr_text": "小明有24个苹果，平均分给6个同学，每人几个？",
        "mock_confidence": 0.94,
    },
)
print("\n## homework_attachment")
print(f"attachment_id: {attachment['attachment_id']}")
print(f"recognized_text: {attachment['recognized_content'].get('text')}")
print(f"needs_input: {attachment['session_state'].get('needs_input')}")
print(f"reply: {attachment['reply']['text']}")

show(
    "learning_help_with_attachment",
    message(
        child_id="child_demo_001",
        session_id="session_demo_attachment",
        text="这是刚才拍的题目",
        device_time="2026-05-18T18:35:00+08:00",
        attachments=[attachment["attachment_id"]],
    ),
)
PY
