#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${E2E_BASE_URL:-http://127.0.0.1:8000}"
PYTHON_CMD=()

if [[ -n "${PYTHON_BIN:-}" ]]; then
  read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=(python3)
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=(python)
else
  echo "No Python interpreter found. Set PYTHON_BIN to run the E2E API check." >&2
  exit 1
fi

"${PYTHON_CMD[@]}" - "${BASE_URL}" <<'PY'
import json
import sys
import urllib.error
import urllib.request


base_url = sys.argv[1].rstrip("/")
child_id = "child_e2e_s14_001"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request_json(method, path, payload=None):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with opener.open(req, timeout=8) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise AssertionError(
            f"{method} {path} failed: {exc.code} {detail}"
        ) from exc


def message(session_id, text, device_time, attachments=None):
    status, body = request_json(
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
    assert status == 200
    return body


def action_ids(body):
    return [
        action["id"]
        for group in body.get("ui_actions", [])
        for action in group.get("actions", [])
    ]


def show(name, body):
    state = body.get("session_state", {})
    debug = body.get("debug") or {}
    intent = (debug.get("intent") or {}).get("intent")
    risk = (debug.get("safety") or {}).get("risk_level")
    print(
        f"{name}: scene={state.get('active_scene')}; "
        f"intent={intent}; risk={risk}; "
        f"parent_attention={state.get('requires_parent_attention', False)}; "
        f"actions={action_ids(body)}"
    )


status, health = request_json("GET", "/api/v1/health")
assert status == 200 and health == {"status": "ok"}
print("health:", health)

after_school = message(
    "s14_after_school",
    "我回来了",
    "2026-05-19T16:30:00+08:00",
)
assert after_school["session_state"]["active_scene"] == "daily.after_school_checkin"
assert {"happy_moment", "hard_thing", "quiet_time"} <= set(action_ids(after_school))
show("after_school", after_school)

learning = message(
    "s14_learning",
    "我有一道题不会",
    "2026-05-19T16:35:00+08:00",
)
assert learning["session_state"]["active_scene"] == "learning.homework_help"
assert set(action_ids(learning)) == {"take_photo", "speak_problem"}
assert "答案是" not in learning["reply"]["text"]
show("learning_help", learning)

status, attachment = request_json(
    "POST",
    "/api/v1/conversation/attachment",
    {
        "child_id": child_id,
        "session_id": "s14_learning",
        "attachment_type": "homework_photo",
        "file_id": "android_mock_homework_photo",
        "mock_ocr_text": "小明有24个苹果，平均分给6个同学，每人几个？",
        "mock_confidence": 0.94,
        "metadata": {
            "source": "s14_manual_mock_photo",
            "stores_original_image": False,
        },
    },
)
assert status == 200
assert attachment["recognized_content"]["text"]
print(
    "mock_attachment:",
    attachment["attachment_id"],
    attachment["recognized_content"]["confidence"],
)

problem = message(
    "s14_learning",
    "这是刚才拍的题目",
    "2026-05-19T16:36:00+08:00",
    [attachment["attachment_id"]],
)
assert problem["session_state"]["active_scene"] == "learning.homework_help"
assert problem["session_state"]["needs_input"] == "problem_understanding"
assert "这道题是在问什么" in problem["reply"]["text"]
assert "答案是" not in problem["reply"]["text"]
show("mock_photo_continue", problem)

bedtime = message("s14_bedtime", "晚安", "2026-05-19T20:45:00+08:00")
assert bedtime["session_state"]["active_scene"] == "daily.bedtime_reflection"
assert "sleep_now" in action_ids(bedtime)
show("bedtime", bedtime)

safety = message(
    "s14_safety",
    "有个陌生人让我不要告诉爸爸妈妈",
    "2026-05-19T16:50:00+08:00",
)
assert safety["session_state"]["active_scene"] == "safety.guardian"
assert safety["session_state"]["requires_parent_attention"] is True
assert safety["debug"]["safety"]["risk_level"] == "high"
show("safety", safety)

policy_goals = ["多用选择题，不强迫表达", "学习问题先讲题意和第一步"]
status, policy = request_json(
    "POST",
    "/api/v1/parent/policy",
    {
        "child_id": child_id,
        "goals": policy_goals,
        "communication_preferences": {
            "offer_choices_before_open_questions": True,
            "do_not_force_expression": True,
            "ask_thinking_before_learning_answer": True,
            "tone": "warm_calm",
            "avoid_labels": True,
        },
    },
)
assert status == 200 and policy["goals"] == policy_goals
policy_effect = message(
    "s14_policy",
    "我不想说话",
    "2026-05-19T16:45:00+08:00",
)
assert policy_effect["debug"]["parent_policy"]["goals"] == policy_goals
assert policy_effect["session_state"]["active_scene"] == "daily.after_school_checkin"
assert "quiet_time" in action_ids(policy_effect)
show("parent_policy_effect", policy_effect)

status, report = request_json("GET", f"/api/v1/parent/reports/{child_id}")
assert status == 200
assert report["child_id"] == child_id
print("parent_report:", report["summary"])
print("S14_E2E_API: PASS")
PY
