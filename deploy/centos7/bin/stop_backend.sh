#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=backend_service_common.sh
source "${SCRIPT_DIR}/backend_service_common.sh"

ensure_runtime_dirs
load_service_env

pid="$(read_pid)"
if ! is_pid_running "${pid}"; then
  rm -f "${PID_FILE}"
  log "BACKEND_STOP: ALREADY_STOPPED"
  exit 0
fi

log "BACKEND_STOP: TERM"
log "pid=${pid}"
kill "${pid}" >/dev/null 2>&1 || true

for _ in $(seq 1 20); do
  if ! is_pid_running "${pid}"; then
    rm -f "${PID_FILE}"
    log "BACKEND_STOP: PASS"
    exit 0
  fi
  sleep 1
done

log "BACKEND_STOP: KILL"
kill -9 "${pid}" >/dev/null 2>&1 || true
rm -f "${PID_FILE}"
log "BACKEND_STOP: PASS"
