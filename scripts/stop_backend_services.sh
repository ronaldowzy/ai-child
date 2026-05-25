#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/backend_services_common.sh
source "${SCRIPT_DIR}/backend_services_common.sh"

AGENT_NAME="${CODEX_AGENT_NAME:-main}"
STOP_ALL=false
FORCE=false
STOP_POSTGRES=false

usage() {
  cat <<'EOF'
Usage: bash scripts/stop_backend_services.sh [options]

Stops FastAPI backend services started by scripts/start_backend_services.sh.
By default this stops only one agent's FastAPI process and keeps shared
PostgreSQL running, so parallel agents do not break each other.

Options:
  --agent NAME        Stop one agent service. Default: CODEX_AGENT_NAME or main.
  --all              Stop all agent-managed FastAPI services.
  --force            Send SIGKILL if SIGTERM does not stop the process.
  --stop-postgres    Also stop local PostgreSQL. Use only when no other agent needs it.
  -h, --help         Show this help.

Examples:
  bash scripts/stop_backend_services.sh --agent lane-a
  bash scripts/stop_backend_services.sh --all
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_NAME="${2:-}"
      shift 2
      ;;
    --all)
      STOP_ALL=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --stop-postgres)
      STOP_POSTGRES=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

stop_one_agent() {
  local agent="$1"
  local service_dir pid_file env_file log_file pid command launchd_label plist_file screen_session
  service_dir="$(service_dir_for_agent "${agent}")"
  pid_file="${service_dir}/backend.pid"
  env_file="${service_dir}/service.env"
  log_file="${service_dir}/backend.log"
  launchd_label=""
  plist_file=""
  screen_session=""
  if [[ -f "${env_file}" ]]; then
    LOG_FILE=""
    LAUNCHD_LABEL=""
    PLIST_FILE=""
    SCREEN_SESSION=""
    # shellcheck source=/dev/null
    source "${env_file}"
    log_file="${LOG_FILE:-${log_file}}"
    launchd_label="${LAUNCHD_LABEL:-}"
    plist_file="${PLIST_FILE:-}"
    screen_session="${SCREEN_SESSION:-}"
  fi

  if [[ ! -f "${pid_file}" ]]; then
    if [[ -n "${plist_file}" && -f "${plist_file}" && "$(uname -s)" == "Darwin" ]]; then
      launchctl bootout "gui/$(id -u)" "${plist_file}" >/dev/null 2>&1 || true
    elif [[ -n "${launchd_label}" && "$(uname -s)" == "Darwin" ]]; then
      launchctl remove "${launchd_label}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${screen_session}" ]] && command -v screen >/dev/null 2>&1; then
      screen -S "${screen_session}" -X quit >/dev/null 2>&1 || true
    fi
    log "BACKEND_SERVICE_STOP: none"
    log "agent=$(sanitize_agent_name "${agent}")"
    return 0
  fi

  pid="$(<"${pid_file}")"
  if ! is_pid_running "${pid}"; then
    if [[ -n "${plist_file}" && -f "${plist_file}" && "$(uname -s)" == "Darwin" ]]; then
      launchctl bootout "gui/$(id -u)" "${plist_file}" >/dev/null 2>&1 || true
    elif [[ -n "${launchd_label}" && "$(uname -s)" == "Darwin" ]]; then
      launchctl remove "${launchd_label}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${screen_session}" ]] && command -v screen >/dev/null 2>&1; then
      screen -S "${screen_session}" -X quit >/dev/null 2>&1 || true
    fi
    log "BACKEND_SERVICE_STOP: stale"
    log "agent=$(sanitize_agent_name "${agent}")"
    log "pid=${pid}"
    rm -f "${pid_file}"
    return 0
  fi

  command="$(pid_command "${pid}")"
  if [[ "${command}" != *"uvicorn app.main:app"* ]]; then
    die "Refusing to stop pid=${pid}; command is not the managed backend: ${command}"
  fi

  log "BACKEND_SERVICE_STOPPING"
  log "agent=$(sanitize_agent_name "${agent}")"
  log "pid=${pid}"
  log "log=${log_file}"
  if [[ -n "${plist_file}" && -f "${plist_file}" && "$(uname -s)" == "Darwin" ]]; then
    launchctl bootout "gui/$(id -u)" "${plist_file}" >/dev/null 2>&1 || true
  elif [[ -n "${launchd_label}" && "$(uname -s)" == "Darwin" ]]; then
    launchctl remove "${launchd_label}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${screen_session}" ]] && command -v screen >/dev/null 2>&1; then
    screen -S "${screen_session}" -X quit >/dev/null 2>&1 || true
  fi
  kill "${pid}" 2>/dev/null || true
  for _ in $(seq 1 20); do
    if ! is_pid_running "${pid}"; then
      rm -f "${pid_file}"
      log "BACKEND_SERVICE_STOPPED"
      log "agent=$(sanitize_agent_name "${agent}")"
      return 0
    fi
    sleep 0.5
  done

  if [[ "${FORCE}" == "true" ]]; then
    kill -KILL "${pid}" 2>/dev/null || true
    rm -f "${pid_file}"
    log "BACKEND_SERVICE_FORCE_STOPPED"
    log "agent=$(sanitize_agent_name "${agent}")"
    return 0
  fi

  die "Backend pid=${pid} did not stop. Re-run with --force if you own this service."
}

stop_postgres() {
  log "POSTGRES_STOP: requested"
  local stopped=false
  local compose_file="${ROOT_DIR}/docker-compose.local.yml"
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    if docker compose -f "${compose_file}" ps postgres >/dev/null 2>&1; then
      docker compose -f "${compose_file}" stop postgres >/dev/null 2>&1 || true
      stopped=true
    fi
  fi
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    if brew services list 2>/dev/null | grep -E '^postgresql@16[[:space:]]+started' >/dev/null 2>&1; then
      brew services stop postgresql@16 >/dev/null 2>&1 || true
      stopped=true
    fi
  fi
  log "POSTGRES_STOP: ${stopped}"
}

if [[ "${STOP_ALL}" == "true" ]]; then
  if [[ -d "${SERVICE_ROOT}" ]]; then
    while IFS= read -r -d '' service_dir; do
      stop_one_agent "$(basename "${service_dir}")"
    done < <(find "${SERVICE_ROOT}" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
  else
    log "BACKEND_SERVICE_STOP: none"
  fi
else
  stop_one_agent "$(sanitize_agent_name "${AGENT_NAME}")"
fi

if [[ "${STOP_POSTGRES}" == "true" ]]; then
  stop_postgres
fi
