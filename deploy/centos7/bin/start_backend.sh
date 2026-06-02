#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=backend_service_common.sh
source "${SCRIPT_DIR}/backend_service_common.sh"

ensure_runtime_dirs
load_service_env
resolve_python_bin

[[ -d "${BACKEND_DIR}" ]] || die "Backend directory not found: ${BACKEND_DIR}"

existing_pid="$(read_pid)"
if is_pid_running "${existing_pid}"; then
  log "BACKEND_ALREADY_RUNNING"
  log "pid=${existing_pid}"
  log "log=${STDOUT_LOG}"
  log "err_log=${STDERR_LOG}"
  exit 0
fi

rm -f "${PID_FILE}"
: >>"${STDOUT_LOG}"
: >>"${STDERR_LOG}"
: >>"${START_LOG}"

host="${CHILD_AI_BACKEND_HOST:-0.0.0.0}"
port="${CHILD_AI_BACKEND_PORT:-22026}"

{
  printf '\n[%s] START\n' "$(date '+%Y-%m-%d %H:%M:%S %z')"
  printf 'app_root=%s\n' "${APP_ROOT}"
  printf 'backend_dir=%s\n' "${BACKEND_DIR}"
  printf 'env_file=%s\n' "${ENV_FILE}"
  printf 'python=%s\n' "${PYTHON_BIN}"
  printf 'host=%s\n' "${host}"
  printf 'port=%s\n' "${port}"
  printf 'stdout_log=%s\n' "${STDOUT_LOG}"
  printf 'stderr_log=%s\n' "${STDERR_LOG}"
} >>"${START_LOG}"

cd "${BACKEND_DIR}"
nohup "${PYTHON_BIN}" -m uvicorn app.main:app --host "${host}" --port "${port}" \
  >>"${STDOUT_LOG}" 2>>"${STDERR_LOG}" &

pid="$!"
printf '%s\n' "${pid}" >"${PID_FILE}"

health_url="$(backend_url)"
for _ in $(seq 1 60); do
  if ! is_pid_running "${pid}"; then
    log "BACKEND_START_FAILED"
    log "pid=${pid}"
    log "stderr_tail=${STDERR_LOG}"
    tail -n 80 "${STDERR_LOG}" || true
    exit 1
  fi
  if curl -fsS --max-time 2 "${health_url}" >/dev/null 2>&1; then
    log "BACKEND_START: PASS"
    log "pid=${pid}"
    log "health_url=${health_url}"
    log "stdout_log=${STDOUT_LOG}"
    log "stderr_log=${STDERR_LOG}"
    exit 0
  fi
  sleep 1
done

log "BACKEND_START: WARN"
log "reason=health_not_ready_within_60s"
log "pid=${pid}"
log "health_url=${health_url}"
log "stdout_log=${STDOUT_LOG}"
log "stderr_log=${STDERR_LOG}"
exit 0
