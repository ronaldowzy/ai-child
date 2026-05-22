#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL=""
VARIANT="debug"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/ [--variant debug]

Notes:
  - This script is for physical Android devices, not the emulator.
  - Do not use http://10.0.2.2:8000/ for Redmi K60 / Honor Pad 5.
EOF
}

capitalize() {
  local value="$1"
  printf '%s%s\n' "$(printf '%s' "${value:0:1}" | tr '[:lower:]' '[:upper:]')" "${value:1}"
}

sha256_file() {
  local file="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${file}" | awk '{print $1}'
    return
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${file}" | awk '{print $1}'
    return
  fi
  echo "sha256_tool_missing" >&2
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="${2:-}"
      shift 2
      ;;
    --variant)
      VARIANT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${BASE_URL}" ]]; then
  echo "DEVICE_APK_BUILD: FAIL" >&2
  echo "reason=missing_base_url" >&2
  usage >&2
  exit 2
fi

if [[ "${BASE_URL}" == "http://10.0.2.2:8000/" || "${BASE_URL}" == "http://10.0.2.2:8000" ]]; then
  echo "DEVICE_APK_BUILD: FAIL" >&2
  echo "reason=emulator_base_url_not_allowed_for_device" >&2
  exit 2
fi

if [[ ! "${BASE_URL}" =~ ^https?://[^[:space:]]+/$ ]]; then
  echo "DEVICE_APK_BUILD: FAIL" >&2
  echo "reason=base_url_must_be_http_or_https_and_end_with_slash" >&2
  usage >&2
  exit 2
fi

variant_lower="$(printf '%s' "${VARIANT}" | tr '[:upper:]' '[:lower:]')"
assemble_task="assemble$(capitalize "${variant_lower}")"

echo "DEVICE_APK_BUILD: START"
echo "variant=${variant_lower}"
echo "base_url=${BASE_URL}"

bash "${ROOT_DIR}/scripts/android_gradle.sh" "${assemble_task}" "-PconversationApiBaseUrl=${BASE_URL}"

apk_dir="${ROOT_DIR}/android/app/build/outputs/apk/${variant_lower}"
apk_path="${apk_dir}/app-${variant_lower}.apk"
if [[ ! -f "${apk_path}" ]]; then
  apk_path="$(find "${apk_dir}" -maxdepth 1 -type f -name '*.apk' -print | sort | tail -n 1)"
fi
if [[ -z "${apk_path}" || ! -f "${apk_path}" ]]; then
  echo "DEVICE_APK_BUILD: FAIL" >&2
  echo "reason=apk_not_found" >&2
  exit 1
fi

size_bytes="$(wc -c < "${apk_path}" | tr -d '[:space:]')"
sha256="$(sha256_file "${apk_path}")"
build_time_utc="$(TZ=UTC date '+%Y-%m-%dT%H:%M:%SZ')"

echo "DEVICE_APK_BUILD: PASS"
echo "apk_path=${apk_path}"
echo "apk_size_bytes=${size_bytes}"
echo "apk_sha256=${sha256}"
echo "base_url=${BASE_URL}"
echo "build_variant=${variant_lower}"
echo "build_time_utc=${build_time_utc}"
