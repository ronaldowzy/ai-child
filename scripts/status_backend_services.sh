#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/backend_services_common.sh
source "${SCRIPT_DIR}/backend_services_common.sh"

AGENT_FILTER=""
PORT_FILTER=""

usage() {
  cat <<'EOF'
Usage: bash scripts/status_backend_services.sh [options]

Shows backend services started by scripts/start_backend_services.sh.

Options:
  --agent NAME    Show one agent service.
  --port PORT     Also inspect a specific local port owner.
  -h, --help      Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_FILTER="$(sanitize_agent_name "${2:-}")"
      shift 2
      ;;
    --port)
      PORT_FILTER="${2:-}"
      shift 2
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

service_dirs=()
if [[ -n "${AGENT_FILTER}" ]]; then
  service_dirs+=("$(service_dir_for_agent "${AGENT_FILTER}")")
elif [[ -d "${SERVICE_ROOT}" ]]; then
  while IFS= read -r -d '' dir; do
    service_dirs+=("${dir}")
  done < <(find "${SERVICE_ROOT}" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
fi

if [[ "${#service_dirs[@]}" -eq 0 ]]; then
  log "BACKEND_SERVICE_STATUS: none"
else
  for service_dir in "${service_dirs[@]}"; do
    agent="$(basename "${service_dir}")"
    pid_file="${service_dir}/backend.pid"
    env_file="${service_dir}/service.env"
    log_file="${service_dir}/backend.log"
    port=""
    host=""
    screen_session=""
    if [[ -f "${env_file}" ]]; then
      AGENT_NAME=""
      HOST=""
      PORT=""
      LOG_FILE=""
      SCREEN_SESSION=""
      # shellcheck source=/dev/null
      source "${env_file}"
      agent="${AGENT_NAME:-${agent}}"
      port="${PORT:-}"
      host="${HOST:-}"
      log_file="${LOG_FILE:-${log_file}}"
      screen_session="${SCREEN_SESSION:-}"
    fi
    pid=""
    if [[ -f "${pid_file}" ]]; then
      pid="$(<"${pid_file}")"
    fi

    status="stopped"
    health="not_checked"
    command=""
    if is_pid_running "${pid}"; then
      status="running"
      command="$(pid_command "${pid}")"
      if [[ -n "${port}" ]] \
        && curl --noproxy '*' -fsS "http://127.0.0.1:${port}/api/v1/health/detail" >/dev/null 2>&1; then
        health="ok"
      else
        health="unreachable"
      fi
    elif [[ -n "${pid}" ]]; then
      status="stale"
    fi

    log "BACKEND_SERVICE_STATUS"
    log "agent=${agent}"
    log "status=${status}"
    log "pid=${pid:-none}"
    log "host=${host:-unknown}"
    log "port=${port:-unknown}"
    log "health=${health}"
    log "log=${log_file}"
    if [[ -n "${screen_session}" ]]; then
      log "screen_session=${screen_session}"
    fi
    if [[ -n "${command}" ]]; then
      log "command=${command}"
    fi
  done
fi

if [[ -n "${PORT_FILTER}" ]]; then
  owner="$(port_owner_pid "${PORT_FILTER}")"
  log "PORT_STATUS"
  log "port=${PORT_FILTER}"
  log "owner_pid=${owner:-none}"
  if [[ -n "${owner}" ]]; then
    log "owner_command=$(pid_command "${owner}")"
  fi
fi
