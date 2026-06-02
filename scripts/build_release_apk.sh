#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/release/app_version.properties"
BASE_URL=""
VARIANT="release"
OUTPUT_DIR="${ROOT_DIR}/dist/apk"
PUBLISH_TO_BACKEND_STORAGE=false
ALLOW_UNSIGNED=false

usage() {
  cat <<'EOF'
Usage:
  bash scripts/build_release_apk.sh --base-url https://api.example.com/ [options]

Options:
  --base-url URL                 Backend public base URL. Must end with /.
  --variant release|debug        Build variant. Default: release.
  --output-dir DIR               Output directory. Default: dist/apk.
  --publish-to-backend-storage   Copy APK to storage/apk/<apkFilename>.
  --allow-unsigned               Allow unsigned release APK output.
  -h, --help                     Show this help.

Release signing:
  Set these environment variables before building a formal release APK:
    CHILD_AI_RELEASE_STORE_FILE
    CHILD_AI_RELEASE_STORE_PASSWORD
    CHILD_AI_RELEASE_KEY_ALIAS
    CHILD_AI_RELEASE_KEY_PASSWORD
EOF
}

capitalize() {
  local value="$1"
  printf '%s%s\n' "$(printf '%s' "${value:0:1}" | tr '[:lower:]' '[:upper:]')" "${value:1}"
}

property_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key { print substr($0, length(key) + 2); exit }' "${VERSION_FILE}"
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
  echo "sha256 tool missing" >&2
  exit 1
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
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --publish-to-backend-storage)
      PUBLISH_TO_BACKEND_STORAGE=true
      shift
      ;;
    --allow-unsigned)
      ALLOW_UNSIGNED=true
      shift
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
  echo "RELEASE_APK_BUILD: FAIL" >&2
  echo "reason=missing_base_url" >&2
  usage >&2
  exit 2
fi
if [[ "${BASE_URL}" == "http://localhost:"* || "${BASE_URL}" == "http://127.0.0.1:"* ]]; then
  echo "RELEASE_APK_BUILD: FAIL" >&2
  echo "reason=base_url_must_not_be_loopback" >&2
  exit 2
fi
if [[ ! "${BASE_URL}" =~ ^https?://[^[:space:]]+/$ ]]; then
  echo "RELEASE_APK_BUILD: FAIL" >&2
  echo "reason=base_url_must_be_http_or_https_and_end_with_slash" >&2
  exit 2
fi
if [[ "${BASE_URL}" == http://* ]]; then
  echo "RELEASE_APK_BUILD: WARN"
  echo "reason=production_https_recommended"
fi

variant_lower="$(printf '%s' "${VARIANT}" | tr '[:upper:]' '[:lower:]')"
if [[ "${variant_lower}" != "release" && "${variant_lower}" != "debug" ]]; then
  echo "--variant must be release or debug." >&2
  exit 2
fi

if [[ "${variant_lower}" == "release" && "${ALLOW_UNSIGNED}" != "true" ]]; then
  missing_signing=()
  [[ -n "${CHILD_AI_RELEASE_STORE_FILE:-}" ]] || missing_signing+=("CHILD_AI_RELEASE_STORE_FILE")
  [[ -n "${CHILD_AI_RELEASE_STORE_PASSWORD:-}" ]] || missing_signing+=("CHILD_AI_RELEASE_STORE_PASSWORD")
  [[ -n "${CHILD_AI_RELEASE_KEY_ALIAS:-}" ]] || missing_signing+=("CHILD_AI_RELEASE_KEY_ALIAS")
  [[ -n "${CHILD_AI_RELEASE_KEY_PASSWORD:-}" ]] || missing_signing+=("CHILD_AI_RELEASE_KEY_PASSWORD")
  if (( ${#missing_signing[@]} > 0 )); then
    echo "RELEASE_APK_BUILD: FAIL" >&2
    echo "reason=missing_release_signing_env" >&2
    printf 'missing=%s\n' "${missing_signing[*]}" >&2
    exit 2
  fi
fi

version_name="$(property_value versionName)"
version_code="$(property_value versionCode)"
apk_filename="$(property_value apkFilename)"
apk_filename="${apk_filename:-child-ai-companion.apk}"
assemble_task="assemble$(capitalize "${variant_lower}")"

echo "RELEASE_APK_BUILD: START"
echo "variant=${variant_lower}"
echo "version_name=${version_name}"
echo "version_code=${version_code}"
echo "base_url=${BASE_URL}"

bash "${ROOT_DIR}/scripts/android_gradle.sh" "${assemble_task}" "-PconversationApiBaseUrl=${BASE_URL}"

apk_dir="${ROOT_DIR}/android/app/build/outputs/apk/${variant_lower}"
apk_path="$(find "${apk_dir}" -maxdepth 1 -type f -name '*.apk' -print | sort | tail -n 1)"
if [[ -z "${apk_path}" || ! -f "${apk_path}" ]]; then
  echo "RELEASE_APK_BUILD: FAIL" >&2
  echo "reason=apk_not_found" >&2
  exit 1
fi
if [[ "${variant_lower}" == "release" && "${apk_path}" == *unsigned* && "${ALLOW_UNSIGNED}" != "true" ]]; then
  echo "RELEASE_APK_BUILD: FAIL" >&2
  echo "reason=release_apk_unsigned" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"
output_apk="${OUTPUT_DIR}/child-ai-companion-v${version_name}-code${version_code}-${variant_lower}.apk"
cp "${apk_path}" "${output_apk}"
short_output_apk="${OUTPUT_DIR}/${apk_filename}"
cp "${output_apk}" "${short_output_apk}"

size_bytes="$(wc -c < "${output_apk}" | tr -d '[:space:]')"
sha256="$(sha256_file "${output_apk}")"
build_time_utc="$(TZ=UTC date '+%Y-%m-%dT%H:%M:%SZ')"
metadata_path="${output_apk%.apk}.metadata"
{
  printf 'apk_path=%s\n' "${output_apk}"
  printf 'apk_size_bytes=%s\n' "${size_bytes}"
  printf 'apk_sha256=%s\n' "${sha256}"
  printf 'base_url=%s\n' "${BASE_URL}"
  printf 'build_variant=%s\n' "${variant_lower}"
  printf 'version_name=%s\n' "${version_name}"
  printf 'version_code=%s\n' "${version_code}"
  printf 'build_time_utc=%s\n' "${build_time_utc}"
} >"${metadata_path}"
printf '%s  %s\n' "${sha256}" "$(basename "${output_apk}")" >"${output_apk}.sha256"
printf '%s  %s\n' "${sha256}" "$(basename "${short_output_apk}")" >"${short_output_apk}.sha256"

if [[ "${PUBLISH_TO_BACKEND_STORAGE}" == "true" ]]; then
  backend_apk_dir="${ROOT_DIR}/storage/apk"
  mkdir -p "${backend_apk_dir}"
  cp "${output_apk}" "${backend_apk_dir}/${apk_filename}"
  echo "backend_storage_apk=${backend_apk_dir}/${apk_filename}"
fi

echo "RELEASE_APK_BUILD: PASS"
cat "${metadata_path}"
echo "short_apk_path=${short_output_apk}"
