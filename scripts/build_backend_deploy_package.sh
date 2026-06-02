#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/release/app_version.properties"
OUTPUT_DIR="${ROOT_DIR}/dist/backend"
INCLUDE_APK=false
INCLUDE_LOCAL_ASR=true
INCLUDE_LOCAL_TTS=false

usage() {
  cat <<'EOF'
Usage:
  bash scripts/build_backend_deploy_package.sh [options]

Options:
  --output-dir DIR       Output directory. Default: dist/backend.
  --include-apk          Include storage/apk/<apkFilename> if present.
  --no-local-asr         Do not include backend/models/asr/sensevoice.
  --include-local-tts    Include local sherpa-onnx TTS model files.
  -h, --help             Show this help.

The package intentionally excludes .env, secrets, logs, tts cache, attachments,
Android build outputs, and local runtime data.
EOF
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

copy_path() {
  local src="$1"
  local dst="$2"
  if [[ -e "${src}" ]]; then
    mkdir -p "$(dirname "${dst}")"
    rsync -a \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      --exclude '.DS_Store' \
      --exclude '._*' \
      --exclude '__MACOSX/' \
      --exclude 'tests/' \
      --exclude '.pytest_cache/' \
      --exclude '.ruff_cache/' \
      "${src}" "${dst}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --include-apk)
      INCLUDE_APK=true
      shift
      ;;
    --no-local-asr)
      INCLUDE_LOCAL_ASR=false
      shift
      ;;
    --include-local-tts)
      INCLUDE_LOCAL_TTS=true
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

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to build the deploy package." >&2
  exit 1
fi

version_name="$(property_value versionName)"
version_code="$(property_value versionCode)"
apk_filename="$(property_value apkFilename)"
apk_filename="${apk_filename:-child-ai-companion.apk}"
git_sha="$(git -C "${ROOT_DIR}" rev-parse --short HEAD 2>/dev/null || echo nogit)"
if [[ "${git_sha}" != "nogit" ]] && {
  ! git -C "${ROOT_DIR}" diff --quiet --ignore-submodules -- ||
    ! git -C "${ROOT_DIR}" diff --cached --quiet --ignore-submodules --
}; then
  git_sha="${git_sha}-dirty"
fi
build_time_utc="$(TZ=UTC date '+%Y%m%dT%H%M%SZ')"
package_name="ai-child-backend-v${version_name}-code${version_code}-${git_sha}-${build_time_utc}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT
staging="${tmp_dir}/${package_name}"
mkdir -p \
  "${staging}/storage/apk" \
  "${staging}/backend/storage/tts_cache" \
  "${staging}/backend/storage/attachments" \
  "${staging}/storage/fox_hd"

copy_path "${ROOT_DIR}/backend/app" "${staging}/backend/"
copy_path "${ROOT_DIR}/backend/alembic" "${staging}/backend/"
copy_path "${ROOT_DIR}/backend/assets/voices" "${staging}/backend/assets/"
copy_path "${ROOT_DIR}/deploy" "${staging}/"
copy_path "${ROOT_DIR}/release" "${staging}/"
copy_path "${ROOT_DIR}/scripts/db_migrate.sh" "${staging}/scripts/"
copy_path "${ROOT_DIR}/scripts/build_backend_deploy_package.sh" "${staging}/scripts/"

cp "${ROOT_DIR}/backend/alembic.ini" "${staging}/backend/alembic.ini"
cp "${ROOT_DIR}/backend/pyproject.toml" "${staging}/backend/pyproject.toml"
cp "${ROOT_DIR}/.env.example" "${staging}/.env.example"
cp "${ROOT_DIR}/deploy/centos7/child-ai-backend.env.example" "${staging}/child-ai-backend.env.example"
cp "${ROOT_DIR}/deploy/centos7/bin/backend_service_common.sh" "${staging}/backend_service_common.sh"
cp "${ROOT_DIR}/deploy/centos7/bin/start_backend.sh" "${staging}/start_backend.sh"
cp "${ROOT_DIR}/deploy/centos7/bin/stop_backend.sh" "${staging}/stop_backend.sh"
cp "${ROOT_DIR}/deploy/centos7/bin/status_backend.sh" "${staging}/status_backend.sh"
cp "${ROOT_DIR}/deploy/centos7/bin/migrate_db.sh" "${staging}/migrate_db.sh"
chmod +x \
  "${staging}/start_backend.sh" \
  "${staging}/stop_backend.sh" \
  "${staging}/status_backend.sh" \
  "${staging}/migrate_db.sh"

if [[ "${INCLUDE_LOCAL_ASR}" == "true" ]]; then
  copy_path "${ROOT_DIR}/backend/models/asr/sensevoice" "${staging}/backend/models/asr/"
fi
if [[ "${INCLUDE_LOCAL_TTS}" == "true" ]]; then
  copy_path "${ROOT_DIR}/backend/models/tts/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia" "${staging}/backend/models/tts/"
  copy_path "${ROOT_DIR}/backend/models/tts/vocos_24khz.onnx" "${staging}/backend/models/tts/"
fi
if [[ "${INCLUDE_APK}" == "true" ]]; then
  apk_path="${ROOT_DIR}/storage/apk/${apk_filename}"
  if [[ ! -f "${apk_path}" ]]; then
    echo "Requested --include-apk but APK is missing: ${apk_path}" >&2
    exit 1
  fi
  cp "${apk_path}" "${staging}/storage/apk/${apk_filename}"
fi

find "${staging}" -name '._*' -type f -delete
find "${staging}" -name '.DS_Store' -type f -delete
find "${staging}" -name '__MACOSX' -type d -prune -exec rm -rf {} +

mkdir -p "${OUTPUT_DIR}"
package_path="${OUTPUT_DIR}/${package_name}.tar.gz"
tar -C "${tmp_dir}" -czf "${package_path}" "${package_name}"

if tar -tzf "${package_path}" | grep -E '(^|/)\._|(^|/)\.DS_Store$|(^|/)__MACOSX(/|$)' >/dev/null; then
  echo "DEPLOY_PACKAGE_BUILD: FAIL" >&2
  echo "reason=macos_metadata_file_in_package" >&2
  tar -tzf "${package_path}" | grep -E '(^|/)\._|(^|/)\.DS_Store$|(^|/)__MACOSX(/|$)' >&2
  exit 1
fi

if tar -tzf "${package_path}" | grep -E '(^|/)\.env($|/)|\.p12$|\.pem$|\.key$|\.crt$' >/dev/null; then
  echo "DEPLOY_PACKAGE_BUILD: FAIL" >&2
  echo "reason=secret_like_file_in_package" >&2
  tar -tzf "${package_path}" | grep -E '(^|/)\.env($|/)|\.p12$|\.pem$|\.key$|\.crt$' >&2
  exit 1
fi

sha256="$(sha256_file "${package_path}")"
size_bytes="$(wc -c < "${package_path}" | tr -d '[:space:]')"
manifest_path="${package_path%.tar.gz}.manifest"
{
  printf 'package_path=%s\n' "${package_path}"
  printf 'package_size_bytes=%s\n' "${size_bytes}"
  printf 'package_sha256=%s\n' "${sha256}"
  printf 'version_name=%s\n' "${version_name}"
  printf 'version_code=%s\n' "${version_code}"
  printf 'git_sha=%s\n' "${git_sha}"
  printf 'build_time_utc=%s\n' "${build_time_utc}"
  printf 'include_local_asr=%s\n' "${INCLUDE_LOCAL_ASR}"
  printf 'include_local_tts=%s\n' "${INCLUDE_LOCAL_TTS}"
  printf 'include_apk=%s\n' "${INCLUDE_APK}"
} >"${manifest_path}"
printf '%s  %s\n' "${sha256}" "$(basename "${package_path}")" >"${package_path}.sha256"

echo "DEPLOY_PACKAGE_BUILD: PASS"
cat "${manifest_path}"
