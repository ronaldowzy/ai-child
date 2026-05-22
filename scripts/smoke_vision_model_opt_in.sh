#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${VISION_SMOKE_BASE_URL:-http://127.0.0.1:8000}"
IMAGE_PATH="${CHILD_AI_VISION_SMOKE_IMAGE:-}"

env_true() {
  local value="${1:-}"
  case "$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

missing=()
model_provider="$(printf '%s' "${CHILD_AI_MODEL_PROVIDER:-}" | tr '[:upper:]' '[:lower:]')"
vision_provider="$(printf '%s' "${CHILD_AI_VISION_PROVIDER:-}" | tr '[:upper:]' '[:lower:]')"
if [[ "${model_provider}" != "mimo" && "${vision_provider}" != "mimo" ]]; then
  missing+=("CHILD_AI_MODEL_PROVIDER=mimo or CHILD_AI_VISION_PROVIDER=mimo")
fi
env_true "${CHILD_AI_MIMO_ENABLED:-}" || missing+=("CHILD_AI_MIMO_ENABLED=true")
env_true "${CHILD_AI_MIMO_ALLOW_IMAGE:-}" || missing+=("CHILD_AI_MIMO_ALLOW_IMAGE=true")
env_true "${CHILD_AI_MIMO_RETENTION_POLICY_CHECKED:-}" || missing+=("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true")
[[ -n "${CHILD_AI_MIMO_API_KEY:-}" ]] || missing+=("CHILD_AI_MIMO_API_KEY")
[[ -n "${IMAGE_PATH}" ]] || missing+=("CHILD_AI_VISION_SMOKE_IMAGE")

if ((${#missing[@]} > 0)); then
  echo "VISION_STATUS=blocked"
  printf 'missing_env=%s\n' "$(IFS=,; printf '%s' "${missing[*]}")"
  exit 0
fi

filename="$(basename "${IMAGE_PATH}")"
if [[ ! "${filename}" =~ (fake|smoke|test|fixture|sample) ]]; then
  echo "VISION_STATUS=blocked"
  echo "reason=image_filename_must_include_fake_smoke_test_fixture_or_sample"
  exit 0
fi
if [[ ! -f "${IMAGE_PATH}" ]]; then
  echo "VISION_STATUS=blocked"
  echo "reason=image_file_not_found"
  exit 0
fi

lower_filename="$(printf '%s' "${filename}" | tr '[:upper:]' '[:lower:]')"
case "${lower_filename}" in
  *.png) mime="image/png" ;;
  *.jpg|*.jpeg) mime="image/jpeg" ;;
  *.webp) mime="image/webp" ;;
  *)
    echo "VISION_STATUS=blocked"
    echo "reason=image_must_be_png_jpeg_or_webp"
    exit 0
    ;;
esac

python3 - "${BASE_URL%/}" "${IMAGE_PATH}" "${mime}" <<'PY'
import base64
import json
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
    with opener.open(request, timeout=45) as response:
        body = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    print("VISION_STATUS=mimo_smoke_fail")
    print(f"status_code={exc.code}")
    raise SystemExit(1)

recognized = body.get("recognized_content", {})
text = recognized.get("text") or ""
print("VISION_STATUS=mimo_smoke_pass")
print(f"provider={recognized.get('provider_name')}")
print(f"model={__import__('os').environ.get('CHILD_AI_MIMO_VISION_MODEL') or __import__('os').environ.get('CHILD_AI_MIMO_MODEL') or 'mimo-v2.5-pro'}")
print(f"recognized_type={recognized.get('type')}")
print(f"text_length={len(text)}")
PY
