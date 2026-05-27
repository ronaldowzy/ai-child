#!/usr/bin/env bash
# 语音链路时间测量脚本
# 测量：LLM 模型时间、文字出现时间、TTS 请求时间、第一段音频时间、总时间
# 支持冷启动（无缓存）和暖启动（有缓存）两次测量
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PORT="${VOICE_MEASURE_PORT:-18092}"
BASE_URL="${VOICE_MEASURE_BASE_URL:-http://127.0.0.1:${PORT}}"
START_SERVER="${VOICE_MEASURE_START_SERVER:-true}"
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
  echo "Backend did not become healthy: ${url}" >&2
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
  echo "=== 启动后端 (mock provider, TTS enabled) ==="
  (
    cd "${BACKEND_DIR}"
    CHILD_AI_ALLOW_MOCK_RUNTIME=true \
    CHILD_AI_MODEL_PROVIDER=mock \
    CHILD_AI_ASR_PROVIDER=mock \
    CHILD_AI_TTS_PROVIDER=mock \
    CHILD_AI_CONVERSATION_TTS_ENABLED=true \
    CHILD_AI_TTS_PUBLIC_BASE_URL=/media/tts \
    "${PYTHON_CMD[@]}" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" --log-level warning
  ) &
  SERVER_PID="$!"
  wait_for_health
  echo "后端已启动"
else
  echo "=== 连接已有后端: ${BASE_URL} ==="
  wait_for_health
fi

echo ""
echo "=== 语音链路时间测量 ==="
echo ""

"${PYTHON_CMD[@]}" - "${BASE_URL}" <<'PY'
import json
import sys
import time
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

TEST_TEXTS = [
    "你好小白狐，我们来聊天吧！",
    "我今天在幼儿园画了一幅画，画的是一只恐龙。",
    "你能告诉我恐龙为什么会灭绝吗？",
]

def send_stream(text: str, label: str) -> dict:
    """发送一次 conversation/stream 请求，返回时间测量结果。"""
    payload = json.dumps({
        "child_id": "measure_child",
        "session_id": f"measure_session_{label}",
        "input": {"type": "text", "text": text, "attachments": []},
        "client_context": {
            "device_time": "2026-05-27T16:00:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
        "stream_options": {
            "protocol_version": "stream.v0.1",
            "text_granularity": "sentence",
            "include_tts": True,
            "audio_delivery": "url",
            "client_turn_id": f"measure_{label}",
        },
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        base_url + "/api/v1/conversation/stream",
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/x-ndjson",
            "X-Request-ID": f"measure-{label}",
        },
        method="POST",
    )

    start = time.perf_counter()
    with opener.open(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    total_ms = (time.perf_counter() - start) * 1000

    events = [json.loads(line) for line in body.splitlines() if line.strip()]
    types = [e["type"] for e in events]

    # 解析各阶段时间
    result = {
        "label": label,
        "input_text_chars": len(text),
        "total_events": len(events),
        "event_types": types,
        "measured_total_ms": round(total_ms, 1),
    }

    # session_started
    session = next((e for e in events if e["type"] == "session_started"), None)
    if session:
        result["stream_mode"] = session["payload"].get("stream_mode")

    # 文字段数
    text_deltas = [e for e in events if e["type"] == "text_delta"]
    result["text_segment_count"] = len(text_deltas)

    # TTS 段数
    tts_started = [e for e in events if e["type"] == "tts_started"]
    audio_ready = [e for e in events if e["type"] == "audio_ready"]
    tts_errors = [e for e in events if e["type"] == "error" and e["payload"].get("stage") == "tts"]
    result["tts_segment_count"] = len(tts_started)
    result["audio_ready_count"] = len(audio_ready)
    result["tts_error_count"] = len(tts_errors)

    # done 事件中的统计
    done = next((e for e in events if e["type"] == "done"), None)
    if done:
        result["done_status"] = done["payload"].get("status")
        result["done_audio_segment_count"] = done["payload"].get("audio_segment_count")

    # 完整回复文字长度
    text_final = next((e for e in events if e["type"] == "text_final"), None)
    if text_final:
        result["reply_text_chars"] = text_final["payload"].get("char_count")
        result["reply_sentence_count"] = text_final["payload"].get("sentence_count")

    return result

print("=" * 60)
print("语音链路时间测量报告")
print("=" * 60)

# 第1轮: 冷启动（可能无缓存）
print("\n--- 第1轮: 冷启动 ---")
cold = send_stream(TEST_TEXTS[0], "cold_1")
print(f"  输入字符数: {cold['input_text_chars']}")
print(f"  回复字符数: {cold.get('reply_text_chars', '?')}")
print(f"  文字段数: {cold['text_segment_count']}")
print(f"  TTS 段数: {cold['tts_segment_count']}")
print(f"  音频就绪数: {cold['audio_ready_count']}")
print(f"  TTS 错误数: {cold['tts_error_count']}")
print(f"  测量总时间: {cold['measured_total_ms']}ms")
print(f"  事件序列: {' -> '.join(cold['event_types'])}")

# 第2轮: 暖启动（相同文本，应该命中缓存）
print("\n--- 第2轮: 暖启动（相同文本，应命中缓存） ---")
warm = send_stream(TEST_TEXTS[0], "warm_1")
print(f"  输入字符数: {warm['input_text_chars']}")
print(f"  回复字符数: {warm.get('reply_text_chars', '?')}")
print(f"  文字段数: {warm['text_segment_count']}")
print(f"  TTS 段数: {warm['tts_segment_count']}")
print(f"  音频就绪数: {warm['audio_ready_count']}")
print(f"  TTS 错误数: {warm['tts_error_count']}")
print(f"  测量总时间: {warm['measured_total_ms']}ms")

# 第3轮: 不同文本
print("\n--- 第3轮: 不同文本 ---")
diff = send_stream(TEST_TEXTS[1], "diff_1")
print(f"  输入字符数: {diff['input_text_chars']}")
print(f"  回复字符数: {diff.get('reply_text_chars', '?')}")
print(f"  文字段数: {diff['text_segment_count']}")
print(f"  TTS 段数: {diff['tts_segment_count']}")
print(f"  音频就绪数: {diff['audio_ready_count']}")
print(f"  TTS 错误数: {diff['tts_error_count']}")
print(f"  测量总时间: {diff['measured_total_ms']}ms")

# 第4轮: 再次暖启动
print("\n--- 第4轮: 暖启动（第3轮文本的缓存） ---")
warm2 = send_stream(TEST_TEXTS[1], "warm_2")
print(f"  输入字符数: {warm2['input_text_chars']}")
print(f"  回复字符数: {warm2.get('reply_text_chars', '?')}")
print(f"  文字段数: {warm2['text_segment_count']}")
print(f"  TTS 段数: {warm2['tts_segment_count']}")
print(f"  音频就绪数: {warm2['audio_ready_count']}")
print(f"  TTS 错误数: {warm2['tts_error_count']}")
print(f"  测量总时间: {warm2['measured_total_ms']}ms")

# 汇总
print("\n" + "=" * 60)
print("时间对比:")
print(f"  冷启动总时间: {cold['measured_total_ms']}ms")
print(f"  暖启动总时间: {warm['measured_total_ms']}ms")
if cold['measured_total_ms'] > 0:
    speedup = cold['measured_total_ms'] - warm['measured_total_ms']
    pct = round(speedup / cold['measured_total_ms'] * 100, 1)
    print(f"  缓存加速: {speedup}ms ({pct}%)")
print("=" * 60)

# 验证关键约束
all_ok = True
for r in [cold, warm, diff, warm2]:
    if r.get("done_status") != "completed":
        print(f"[FAIL] {r['label']}: done_status={r.get('done_status')}")
        all_ok = False
    if r["audio_ready_count"] < 1:
        print(f"[FAIL] {r['label']}: 无音频就绪事件")
        all_ok = False

if all_ok:
    print("\nVOICE_PIPELINE_MEASURE: PASS")
else:
    print("\nVOICE_PIPELINE_MEASURE: FAIL")
    sys.exit(1)
PY
