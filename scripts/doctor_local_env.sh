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
    status_line "adb devices" "WARN" "no connected Android device or emulator"
  fi
else
  status_line "adb" "FAIL" "not found after loading scripts/android_env.sh"
fi

if [[ -x "${ANDROID_HOME:-}/emulator/emulator" ]]; then
  AVD_LIST="$("${ANDROID_HOME}/emulator/emulator" -list-avds 2>/dev/null || true)"
  if [[ -n "${AVD_LIST}" ]]; then
    status_line "Android AVD" "OK" "$(echo "${AVD_LIST}" | tr '\n' ' ')"
  else
    status_line "Android AVD" "WARN" "emulator exists, but no AVD is configured"
  fi
else
  status_line "Android emulator" "WARN" "emulator binary not installed"
fi

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
