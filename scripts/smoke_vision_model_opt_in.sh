#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PORT="${VISION_SMOKE_PORT:-18093}"
BASE_URL="${VISION_SMOKE_BASE_URL:-http://127.0.0.1:${PORT}}"
START_SERVER="${VISION_SMOKE_START_SERVER:-true}"
SERVER_PID=""

env_true() {
  local value="${1:-}"
  case "$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

load_dotenv() {
  if [[ "${VISION_SMOKE_LOAD_DOTENV:-true}" != "true" ]]; then
    echo "dotenv_loaded=false"
    return
  fi
  if [[ ! -f "${ROOT_DIR}/.env" ]]; then
    echo "dotenv_loaded=false"
    return
  fi

  set -a
  set +u
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.env"
  set -u
  set +a
  echo "dotenv_loaded=true"
}

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

generate_fake_png() {
  local target="$1"
  mkdir -p "$(dirname "${target}")"
  "${PYTHON_CMD[@]}" - "${target}" <<'PY'
import struct
import sys
import zlib

path = sys.argv[1]
width = height = 96
rows = []
for y in range(height):
    row = bytearray([0])
    for x in range(width):
        if x < 48 and y < 48:
            row.extend((240, 248, 255))
        elif x >= 48 and y < 48:
            row.extend((255, 230, 180))
        elif x < 48:
            row.extend((180, 230, 190))
        else:
            row.extend((60, 90, 150))
    rows.append(bytes(row))
raw = b"".join(rows)

def chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

png = (
    b"\x89PNG\r\n\x1a\n"
    + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    + chunk(b"IDAT", zlib.compress(raw, 9))
    + chunk(b"IEND", b"")
)
with open(path, "wb") as fh:
    fh.write(png)
PY
}

safe_image_path() {
  local provided_path="${CHILD_AI_VISION_SMOKE_IMAGE:-}"
  local lower_name
  if [[ -n "${provided_path}" ]]; then
    lower_name="$(basename "${provided_path}" | tr '[:upper:]' '[:lower:]')"
    case "${lower_name}" in
      *fake*|*smoke*|*test*|*fixture*|*sample*)
        if [[ -f "${provided_path}" ]]; then
          printf '%s\n' "${provided_path}"
          return
        fi
        ;;
    esac
  fi

  local generated_path="${TMPDIR:-/tmp}/child-ai-vision-smoke/fake_vision_smoke_test.png"
  generate_fake_png "${generated_path}"
  printf '%s\n' "${generated_path}"
}

image_mime() {
  local lower_filename
  lower_filename="$(basename "$1" | tr '[:upper:]' '[:lower:]')"
  case "${lower_filename}" in
    *.png) printf 'image/png\n' ;;
    *.jpg|*.jpeg) printf 'image/jpeg\n' ;;
    *.webp) printf 'image/webp\n' ;;
    *)
      echo "VISION_STATUS=mimo_smoke_fail"
      echo "reason=image_must_be_png_jpeg_or_webp"
      return 1
      ;;
  esac
}

wait_for_health() {
  local url="${BASE_URL%/}/api/v1/health"
  for _ in $(seq 1 100); do
    if curl --noproxy '*' -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "VISION_STATUS=mimo_smoke_fail"
  echo "reason=temporary_backend_not_healthy"
  return 1
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

start_backend_if_needed() {
  if [[ "${START_SERVER}" != "true" ]]; then
    wait_for_health
    return
  fi

  (
    cd "${BACKEND_DIR}"
    "${PYTHON_CMD[@]}" -m uvicorn app.main:app \
      --host 127.0.0.1 \
      --port "${PORT}" \
      --log-level warning
  ) &
  SERVER_PID="$!"
  wait_for_health
}

load_dotenv
resolve_python_cmd

if [[ -z "${CHILD_AI_MIMO_API_KEY:-}" && -n "${CHILD_AI_MIMO_KEY:-}" ]]; then
  export CHILD_AI_MIMO_API_KEY="${CHILD_AI_MIMO_KEY}"
fi
if [[ -z "${CHILD_AI_MIMO_API_KEY:-}" ]]; then
  echo "mimo_key_present=false"
  echo "VISION_STATUS=blocked"
  echo "reason=missing_mimo_key"
  exit 2
fi

export CHILD_AI_VISION_PROVIDER="mimo"
export CHILD_AI_MIMO_ENABLED="true"
export CHILD_AI_MIMO_ALLOW_IMAGE="true"
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED="true"
export CHILD_AI_MIMO_TIMEOUT_MS="${CHILD_AI_MIMO_TIMEOUT_MS:-30000}"
export CHILD_AI_MIMO_VISION_MODEL="${CHILD_AI_MIMO_VISION_MODEL:-mimo-v2.5}"

image_path="$(safe_image_path)"
mime="$(image_mime "${image_path}")"
export CHILD_AI_VISION_SMOKE_IMAGE="${image_path}"

echo "vision_model_path_implemented=yes"
echo "mimo_key_present=true"
echo "smoke_env_overlay=applied"
if [[ "$(basename "${image_path}")" == "fake_vision_smoke_test.png" ]]; then
  echo "smoke_image=generated_fake_test_image"
else
  echo "smoke_image=provided_non_child_test_image"
fi
echo "VISION_STATUS=mimo_ready"

start_backend_if_needed

"${PYTHON_CMD[@]}" - "${BASE_URL%/}" "${image_path}" "${mime}" <<'PY'
import base64
import json
import os
import sys
import urllib.error
import urllib.request

base_url, image_path, mime = sys.argv[1:4]
with open(image_path, "rb") as fh:
    data_uri = f"data:{mime};base64," + base64.b64encode(fh.read()).decode("ascii")

payload = {
    "child_id": "child_vision_smoke",
    "session_id": "session_vision_smoke",
    "attachment_type": "image",
    "image_purpose": "ask_what_is_this",
    "image_data_uri": data_uri,
    "child_caption": "这是一张开发 smoke 测试图片。",
}
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json",
    "X-Request-ID": "vision-model-smoke",
}
request = urllib.request.Request(
    base_url + "/api/v1/conversation/attachment",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers=headers,
    method="POST",
)
try:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    print("VISION_STATUS=mimo_smoke_fail")
    print(f"status_code={exc.code}")
    raise SystemExit(1)
except urllib.error.URLError as exc:
    print("VISION_STATUS=mimo_smoke_fail")
    print(f"error_type={exc.__class__.__name__}")
    raise SystemExit(1)

recognized = body.get("recognized_content", {})
text = recognized.get("text") or ""
provider = recognized.get("provider_name") or ""
model = (
    os.environ.get("CHILD_AI_MIMO_VISION_MODEL")
    or os.environ.get("CHILD_AI_MIMO_MODEL")
    or "mimo-v2.5-pro"
)
if provider != "mimo":
    print("VISION_STATUS=mimo_smoke_fail")
    print(f"provider={provider}")
    print(f"model={model}")
    print("error_type=provider_fallback_or_policy_blocked")
    raise SystemExit(1)

print("VISION_STATUS=mimo_smoke_pass")
print(f"provider={provider}")
print(f"model={model}")
print(f"recognized_type={recognized.get('type')}")
print(f"text_length={len(text)}")
PY
