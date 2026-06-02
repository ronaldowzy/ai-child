#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=backend_service_common.sh
source "${SCRIPT_DIR}/backend_service_common.sh"

ensure_runtime_dirs
load_service_env

pid="$(read_pid)"
health_url="$(backend_url)"

if is_pid_running "${pid}"; then
  log "BACKEND_STATUS: RUNNING"
  log "pid=${pid}"
  log "command=$(pid_command "${pid}")"
else
  log "BACKEND_STATUS: STOPPED"
  log "pid=${pid:-none}"
fi

if curl -fsS --max-time 3 "${health_url}" >/dev/null 2>&1; then
  log "health=ok"
else
  log "health=not_ok"
fi

log "health_url=${health_url}"
log "stdout_log=${STDOUT_LOG}"
log "stderr_log=${STDERR_LOG}"
log "start_log=${START_LOG}"
