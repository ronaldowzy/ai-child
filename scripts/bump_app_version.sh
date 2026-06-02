#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/release/app_version.properties"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/bump_app_version.sh --version-name 0.3.0 [options]
  bash scripts/bump_app_version.sh --bump patch [options]

Options:
  --version-name NAME    New Android versionName, for example 0.3.0.
  --version-code CODE    New Android versionCode. Defaults to current + 1.
  --bump LEVEL           Bump current versionName by patch, minor, or major.
  --title TEXT           Update dialog title. Defaults to "发现新版本 v<versionName>".
  --content TEXT         Update dialog content. Newlines are stored as \n.
  --force-update BOOL    true or false. Defaults to current setting.
  -h, --help             Show this help.

Rules:
  - Formal releases must increase versionCode.
  - This script updates release/app_version.properties only.
EOF
}

property_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key { print substr($0, length(key) + 2); exit }' "${VERSION_FILE}"
}

bump_semver() {
  local current="$1"
  local level="$2"
  IFS=. read -r major minor patch <<<"${current}"
  major="${major:-0}"
  minor="${minor:-0}"
  patch="${patch:-0}"
  case "${level}" in
    patch)
      patch=$((patch + 1))
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    *)
      echo "Unknown bump level: ${level}" >&2
      exit 2
      ;;
  esac
  printf '%s.%s.%s\n' "${major}" "${minor}" "${patch}"
}

VERSION_NAME=""
VERSION_CODE=""
BUMP_LEVEL=""
UPDATE_TITLE=""
UPDATE_CONTENT=""
FORCE_UPDATE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version-name)
      VERSION_NAME="${2:-}"
      shift 2
      ;;
    --version-code)
      VERSION_CODE="${2:-}"
      shift 2
      ;;
    --bump)
      BUMP_LEVEL="${2:-}"
      shift 2
      ;;
    --title)
      UPDATE_TITLE="${2:-}"
      shift 2
      ;;
    --content)
      UPDATE_CONTENT="${2:-}"
      shift 2
      ;;
    --force-update)
      FORCE_UPDATE="${2:-}"
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

if [[ ! -f "${VERSION_FILE}" ]]; then
  echo "Version file not found: ${VERSION_FILE}" >&2
  exit 1
fi

CURRENT_VERSION_NAME="$(property_value versionName)"
CURRENT_VERSION_CODE="$(property_value versionCode)"
CURRENT_FORCE_UPDATE="$(property_value forceUpdate)"
APK_FILENAME="$(property_value apkFilename)"

if [[ -n "${BUMP_LEVEL}" ]]; then
  if [[ -n "${VERSION_NAME}" ]]; then
    echo "Use either --bump or --version-name, not both." >&2
    exit 2
  fi
  VERSION_NAME="$(bump_semver "${CURRENT_VERSION_NAME}" "${BUMP_LEVEL}")"
fi

if [[ -z "${VERSION_NAME}" ]]; then
  echo "Missing --version-name or --bump." >&2
  usage >&2
  exit 2
fi

if [[ -z "${VERSION_CODE}" ]]; then
  VERSION_CODE=$((CURRENT_VERSION_CODE + 1))
fi

if [[ ! "${VERSION_CODE}" =~ ^[0-9]+$ ]]; then
  echo "--version-code must be a positive integer." >&2
  exit 2
fi

if (( VERSION_CODE <= CURRENT_VERSION_CODE )); then
  echo "versionCode must increase: current=${CURRENT_VERSION_CODE}, new=${VERSION_CODE}" >&2
  exit 2
fi

if [[ -z "${UPDATE_TITLE}" ]]; then
  UPDATE_TITLE="发现新版本 v${VERSION_NAME}"
fi
if [[ -z "${UPDATE_CONTENT}" ]]; then
  UPDATE_CONTENT="修复了一些问题"
fi
if [[ -z "${FORCE_UPDATE}" ]]; then
  FORCE_UPDATE="${CURRENT_FORCE_UPDATE:-false}"
fi
if [[ "${FORCE_UPDATE}" != "true" && "${FORCE_UPDATE}" != "false" ]]; then
  echo "--force-update must be true or false." >&2
  exit 2
fi
if [[ -z "${APK_FILENAME}" ]]; then
  APK_FILENAME="child-ai-companion.apk"
fi

UPDATE_CONTENT="${UPDATE_CONTENT//$'\n'/\\n}"

tmp_file="$(mktemp)"
{
  printf 'versionCode=%s\n' "${VERSION_CODE}"
  printf 'versionName=%s\n' "${VERSION_NAME}"
  printf 'updateTitle=%s\n' "${UPDATE_TITLE}"
  printf 'updateContent=%s\n' "${UPDATE_CONTENT}"
  printf 'forceUpdate=%s\n' "${FORCE_UPDATE}"
  printf 'apkFilename=%s\n' "${APK_FILENAME}"
} >"${tmp_file}"
mv "${tmp_file}" "${VERSION_FILE}"

echo "APP_VERSION_BUMP: PASS"
echo "old_version_name=${CURRENT_VERSION_NAME}"
echo "old_version_code=${CURRENT_VERSION_CODE}"
echo "new_version_name=${VERSION_NAME}"
echo "new_version_code=${VERSION_CODE}"
echo "force_update=${FORCE_UPDATE}"
