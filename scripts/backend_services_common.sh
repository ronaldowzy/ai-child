#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
SERVICE_ROOT="${CHILD_AI_SERVICE_ROOT:-${TMPDIR:-/tmp}/ai-child-services}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-child-ai}"

log() {
  printf '%s\n' "$*"
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

sanitize_agent_name() {
  local raw="${1:-main}"
  raw="${raw//[^A-Za-z0-9_.-]/-}"
  if [[ -z "${raw}" ]]; then
    raw="main"
  fi
  printf '%s\n' "${raw}"
}

service_dir_for_agent() {
  local agent
  agent="$(sanitize_agent_name "$1")"
  printf '%s/%s\n' "${SERVICE_ROOT}" "${agent}"
}

load_dotenv() {
  if [[ -f "${ROOT_DIR}/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${ROOT_DIR}/.env"
    set +a
    log "Loaded ${ROOT_DIR}/.env"
  else
    log "No .env found; formal runtime guard may block startup if required provider settings are missing."
  fi
}

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi

  local conda_cmd=""
  if command -v conda >/dev/null 2>&1; then
    conda_cmd="$(command -v conda)"
  elif [[ -x "/opt/homebrew/bin/conda" ]]; then
    conda_cmd="/opt/homebrew/bin/conda"
  elif [[ -x "/opt/homebrew/Caskroom/miniforge/base/condabin/conda" ]]; then
    conda_cmd="/opt/homebrew/Caskroom/miniforge/base/condabin/conda"
  fi

  if [[ -n "${conda_cmd}" ]] \
    && "${conda_cmd}" env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
    local conda_python=""
    conda_python="$(
      "${conda_cmd}" run --no-capture-output -n "${CONDA_ENV_NAME}" \
        python -c 'import sys; print(sys.executable)' 2>/dev/null | tail -n 1
    )"
    if [[ -n "${conda_python}" && -x "${conda_python}" ]]; then
      PYTHON_CMD=("${conda_python}")
      return
    fi
    PYTHON_CMD=("${conda_cmd}" run --no-capture-output -n "${CONDA_ENV_NAME}" python)
    return
  fi

  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi

  die "No Python interpreter found. Set PYTHON_BIN or install/activate ${CONDA_ENV_NAME}."
}

is_pid_running() {
  local pid="${1:-}"
  [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1
}

pid_command() {
  local pid="${1:-}"
  if [[ -z "${pid}" ]]; then
    return 0
  fi
  ps -p "${pid}" -o command= 2>/dev/null || true
}

port_owner_pid() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN -t 2>/dev/null | head -n 1 || true
}

wait_for_backend_health() {
  local host="$1"
  local port="$2"
  local timeout_seconds="${3:-45}"
  local url="http://127.0.0.1:${port}/api/v1/health/detail"
  local started
  started="$(date +%s)"
  while true; do
    if curl --noproxy '*' -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    if (( $(date +%s) - started >= timeout_seconds )); then
      log "Backend health did not become ready at ${url} within ${timeout_seconds}s."
      return 1
    fi
    sleep 1
  done
}
