#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_app_root() {
  if [[ -d "${SCRIPT_DIR}/backend" ]]; then
    printf '%s\n' "${SCRIPT_DIR}"
    return
  fi
  if [[ -d "${SCRIPT_DIR}/../../../backend" ]]; then
    (cd "${SCRIPT_DIR}/../../.." && pwd)
    return
  fi
  printf '%s\n' "/opt/ai-child"
}

APP_ROOT="${AI_CHILD_APP_ROOT:-$(detect_app_root)}"
ENV_FILE="${AI_CHILD_ENV_FILE:-${APP_ROOT}/child-ai-backend.env}"
RUN_DIR="${AI_CHILD_RUN_DIR:-${APP_ROOT}/run}"
LOG_DIR="${AI_CHILD_LOG_DIR:-${APP_ROOT}/logs}"
BACKEND_DIR="${APP_ROOT}/backend"
PID_FILE="${RUN_DIR}/child-ai-backend.pid"
STDOUT_LOG="${LOG_DIR}/child-ai-backend.log"
STDERR_LOG="${LOG_DIR}/child-ai-backend.err.log"
START_LOG="${LOG_DIR}/child-ai-backend.start.log"

log() {
  printf '%s\n' "$*"
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

ensure_runtime_dirs() {
  mkdir -p "${RUN_DIR}" "${LOG_DIR}"
}

load_service_env() {
  [[ -f "${ENV_FILE}" ]] || die "Env file not found: ${ENV_FILE}"
  set -a
  # shellcheck source=/dev/null
  source "${ENV_FILE}"
  set +a

  APP_ROOT="${AI_CHILD_APP_ROOT:-${APP_ROOT}}"
  ENV_FILE="${AI_CHILD_ENV_FILE:-${ENV_FILE}}"
  RUN_DIR="${AI_CHILD_RUN_DIR:-${APP_ROOT}/run}"
  LOG_DIR="${AI_CHILD_LOG_DIR:-${APP_ROOT}/logs}"
  BACKEND_DIR="${APP_ROOT}/backend"
  PID_FILE="${RUN_DIR}/child-ai-backend.pid"
  STDOUT_LOG="${LOG_DIR}/child-ai-backend.log"
  STDERR_LOG="${LOG_DIR}/child-ai-backend.err.log"
  START_LOG="${LOG_DIR}/child-ai-backend.start.log"
}

resolve_python_bin() {
  if [[ -n "${AI_CHILD_PYTHON_BIN:-}" ]]; then
    PYTHON_BIN="${AI_CHILD_PYTHON_BIN}"
  elif [[ -n "${PYTHON_BIN:-}" ]]; then
    PYTHON_BIN="${PYTHON_BIN}"
  elif [[ -x "/opt/conda/envs/child-ai/bin/python" ]]; then
    PYTHON_BIN="/opt/conda/envs/child-ai/bin/python"
  elif [[ -x "/opt/miniconda3/envs/child-ai/bin/python" ]]; then
    PYTHON_BIN="/opt/miniconda3/envs/child-ai/bin/python"
  elif [[ -x "/root/miniconda3/envs/child-ai/bin/python" ]]; then
    PYTHON_BIN="/root/miniconda3/envs/child-ai/bin/python"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    die "Python not found. Set AI_CHILD_PYTHON_BIN in ${ENV_FILE}."
  fi

  [[ -x "${PYTHON_BIN}" ]] || die "Python is not executable: ${PYTHON_BIN}"
}

read_pid() {
  if [[ -f "${PID_FILE}" ]]; then
    tr -d '[:space:]' <"${PID_FILE}"
  fi
}

is_pid_running() {
  local pid="${1:-}"
  [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1
}

pid_command() {
  local pid="${1:-}"
  if [[ -n "${pid}" ]]; then
    ps -p "${pid}" -o command= 2>/dev/null || true
  fi
}

backend_url() {
  local port="${CHILD_AI_BACKEND_PORT:-22026}"
  printf 'http://127.0.0.1:%s/api/v1/health/detail\n' "${port}"
}
