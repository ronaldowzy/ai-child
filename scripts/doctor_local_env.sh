#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-child-ai}"
CONDA_CMD=""

find_conda() {
  if command -v conda >/dev/null 2>&1; then
    CONDA_CMD="$(command -v conda)"
    return
  fi

  if [[ -x "/opt/homebrew/bin/conda" ]]; then
    CONDA_CMD="/opt/homebrew/bin/conda"
    return
  fi

  if [[ -x "${HOME}/miniforge3/bin/conda" ]]; then
    CONDA_CMD="${HOME}/miniforge3/bin/conda"
    return
  fi

  if [[ -x "${HOME}/miniconda3/bin/conda" ]]; then
    CONDA_CMD="${HOME}/miniconda3/bin/conda"
    return
  fi
}

status_line() {
  local name="$1"
  local status="$2"
  local detail="$3"
  printf '%-24s %-8s %s\n' "${name}" "${status}" "${detail}"
}

echo "Local environment doctor"
echo "root: ${ROOT_DIR}"
echo

find_conda
if [[ -n "${CONDA_CMD}" ]]; then
  if "${CONDA_CMD}" env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
    PY_VERSION="$("${CONDA_CMD}" run --no-capture-output -n "${CONDA_ENV_NAME}" python --version 2>&1)"
    status_line "conda ${CONDA_ENV_NAME}" "OK" "${CONDA_CMD}; ${PY_VERSION}"
  else
    status_line "conda ${CONDA_ENV_NAME}" "WARN" "${CONDA_CMD}; env not found"
  fi
else
  status_line "conda" "WARN" "not found on PATH or common Homebrew/miniforge locations"
fi

if command -v python3 >/dev/null 2>&1; then
  status_line "system python3" "INFO" "$(python3 --version 2>&1)"
else
  status_line "system python3" "INFO" "not found"
fi

check_visual_kind_migration() {
  local python_runner=()
  if [[ -n "${CONDA_CMD}" ]] && "${CONDA_CMD}" env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
    python_runner=("${CONDA_CMD}" run --no-capture-output -n "${CONDA_ENV_NAME}" python)
  elif command -v python3 >/dev/null 2>&1; then
    python_runner=(python3)
  elif command -v python >/dev/null 2>&1; then
    python_runner=(python)
  else
    status_line "db migration" "WARN" "python not available for migration check"
    return
  fi

  local migration_output
  migration_output="$(
    cd "${ROOT_DIR}/backend"
    "${python_runner[@]}" - <<'PY' 2>&1
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal

try:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
        inspector = inspect(session.get_bind())
        columns = {column["name"] for column in inspector.get_columns("companion_objects")}
except SQLAlchemyError as exc:
    print(f"STATUS=WARN detail=db_unavailable error_type={exc.__class__.__name__}")
except Exception as exc:
    print(f"STATUS=WARN detail=migration_check_failed error_type={exc.__class__.__name__}")
else:
    if "visual_kind" in columns:
        print("STATUS=OK detail=companion_objects.visual_kind present")
    else:
        print("STATUS=WARN detail=companion_objects.visual_kind missing; run bash scripts/db_migrate.sh")
PY
  )"
  local status detail
  status="$(awk '/^STATUS=/{sub(/^STATUS=/, "", $1); print $1}' <<<"${migration_output}" | tail -n 1)"
  detail="$(awk '/^STATUS=/{sub(/^STATUS=[^ ]* detail=/, ""); print}' <<<"${migration_output}" | tail -n 1)"
  if [[ -n "${status}" ]]; then
    status_line "db migration" "${status}" "${detail}"
  else
    status_line "db migration" "WARN" "migration check produced no status"
  fi
}

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

if command -v java >/dev/null 2>&1; then
  JAVA_VERSION="$(java -version 2>&1 | head -n 1)"
  status_line "JDK" "OK" "${JAVA_HOME:-}; ${JAVA_VERSION}"
else
  status_line "JDK" "FAIL" "java not found after loading scripts/android_env.sh"
fi

if [[ -n "${ANDROID_HOME:-}" && -d "${ANDROID_HOME}" ]]; then
  status_line "Android SDK" "OK" "${ANDROID_HOME}"
else
  status_line "Android SDK" "FAIL" "ANDROID_HOME not found"
fi

if command -v adb >/dev/null 2>&1; then
  ADB_VERSION="$(adb version | head -n 1)"
  status_line "adb" "OK" "${ADB_VERSION}"
  DEVICE_LINES="$(adb devices | awk 'NR > 1 && NF >= 2 {print $0}')"
  if [[ -n "${DEVICE_LINES}" ]]; then
    status_line "adb devices" "OK" "$(echo "${DEVICE_LINES}" | tr '\n' '; ')"
  else
    status_line "adb devices" "WARN" "no connected physical Android device"
  fi
else
  status_line "adb" "FAIL" "not found after loading scripts/android_env.sh"
fi

check_visual_kind_migration

DEFAULT_IFACE="$(route get default 2>/dev/null | awk '/interface:/ {print $2; exit}')"
LAN_IP=""
if [[ -n "${DEFAULT_IFACE}" ]]; then
  LAN_IP="$(ipconfig getifaddr "${DEFAULT_IFACE}" 2>/dev/null || true)"
fi
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
fi
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi
if [[ -n "${LAN_IP}" ]]; then
  status_line "LAN IP" "INFO" "${LAN_IP}${DEFAULT_IFACE:+ (${DEFAULT_IFACE})}"
else
  status_line "LAN IP" "WARN" "not found; check Wi-Fi/network interface"
fi
