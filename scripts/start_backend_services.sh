#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/backend_services_common.sh
source "${SCRIPT_DIR}/backend_services_common.sh"

AGENT_NAME="${CODEX_AGENT_NAME:-main}"
HOST="${CHILD_AI_BACKEND_HOST:-0.0.0.0}"
PORT="${CHILD_AI_BACKEND_PORT:-8000}"
RUN_POSTGRES=true
RUN_MIGRATIONS=true
WAIT_FOR_HEALTH=true
FOREGROUND=false

usage() {
  cat <<'EOF'
Usage: bash scripts/start_backend_services.sh [options]

Starts the local backend service set through the single agent-safe entrypoint.
All Codex agents must use this script instead of hand-written uvicorn/nohup/launchctl.

Options:
  --agent NAME        Service owner name. Default: CODEX_AGENT_NAME or main.
  --host HOST         FastAPI bind host. Default: 0.0.0.0.
  --port PORT         FastAPI port. Default: CHILD_AI_BACKEND_PORT or 8000.
  --skip-postgres    Do not start/setup local PostgreSQL.
  --skip-migrations  Do not run DB setup/migrations; assumes DB is already ready.
  --no-wait          Do not wait for /api/v1/health/detail.
  --foreground       Run FastAPI in the foreground through the same env checks.
  -h, --help         Show this help.

Examples:
  bash scripts/start_backend_services.sh --agent main --port 8000
  bash scripts/start_backend_services.sh --agent lane-a --port 18081 --skip-postgres
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT_NAME="${2:-}"
      shift 2
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --skip-postgres)
      RUN_POSTGRES=false
      shift
      ;;
    --skip-migrations)
      RUN_MIGRATIONS=false
      shift
      ;;
    --no-wait)
      WAIT_FOR_HEALTH=false
      shift
      ;;
    --foreground)
      FOREGROUND=true
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

AGENT_NAME="$(sanitize_agent_name "${AGENT_NAME}")"
[[ -n "${HOST}" ]] || die "--host must not be empty"
[[ "${PORT}" =~ ^[0-9]+$ ]] || die "--port must be a number"

SERVICE_DIR="$(service_dir_for_agent "${AGENT_NAME}")"
PID_FILE="${SERVICE_DIR}/backend.pid"
ENV_FILE="${SERVICE_DIR}/service.env"
LOG_FILE="${SERVICE_DIR}/backend.log"
ERR_LOG_FILE="${SERVICE_DIR}/backend.err.log"
RUNNER_FILE="${SERVICE_DIR}/run_backend.sh"
PLIST_FILE="${SERVICE_DIR}/backend.plist"
LAUNCHD_LABEL="com.ai-child.backend.${AGENT_NAME//_/-}"
SCREEN_SESSION="ai-child-backend-${AGENT_NAME}"

mkdir -p "${SERVICE_DIR}"
load_dotenv
resolve_python_cmd

if [[ "${RUN_POSTGRES}" == "true" ]]; then
  if [[ "${RUN_MIGRATIONS}" == "true" ]]; then
    log "Starting local PostgreSQL and running migrations/smoke through setup_local_postgres.sh."
    bash "${ROOT_DIR}/scripts/setup_local_postgres.sh"
  else
    log "Skipping PostgreSQL setup/migrations; assuming configured database is already ready."
  fi
elif [[ "${RUN_MIGRATIONS}" == "true" ]]; then
  log "Running migrations against configured database."
  bash "${ROOT_DIR}/scripts/db_migrate.sh"
fi

PORT_OWNER="$(port_owner_pid "${PORT}")"
if [[ -n "${PORT_OWNER}" ]]; then
  EXISTING_AGENT_PID=""
  if [[ -f "${PID_FILE}" ]]; then
    EXISTING_AGENT_PID="$(<"${PID_FILE}")"
  fi
  if [[ "${PORT_OWNER}" != "${EXISTING_AGENT_PID}" ]]; then
    die "Port ${PORT} is already owned by pid=${PORT_OWNER}. Use status_backend_services.sh, stop the owning agent, or choose another --port."
  fi
fi

if [[ -f "${PID_FILE}" ]]; then
  EXISTING_PID="$(<"${PID_FILE}")"
  if is_pid_running "${EXISTING_PID}"; then
    log "BACKEND_SERVICE_ALREADY_RUNNING"
    log "agent=${AGENT_NAME}"
    log "pid=${EXISTING_PID}"
    log "port=${PORT}"
    log "log=${LOG_FILE}"
    if [[ "${WAIT_FOR_HEALTH}" == "true" ]]; then
      wait_for_backend_health "${HOST}" "${PORT}" 10 || true
    fi
    exit 0
  fi
fi

cat >"${ENV_FILE}" <<EOF
AGENT_NAME=${AGENT_NAME}
HOST=${HOST}
PORT=${PORT}
LOG_FILE=${LOG_FILE}
ERR_LOG_FILE=${ERR_LOG_FILE}
RUNNER_FILE=${RUNNER_FILE}
PLIST_FILE=${PLIST_FILE}
LAUNCHD_LABEL=${LAUNCHD_LABEL}
SCREEN_SESSION=${SCREEN_SESSION}
ROOT_DIR=${ROOT_DIR}
BACKEND_DIR=${BACKEND_DIR}
STARTED_AT_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

log "BACKEND_SERVICE_START"
log "agent=${AGENT_NAME}"
log "host=${HOST}"
log "port=${PORT}"
log "log=${LOG_FILE}"
log "python=${PYTHON_CMD[*]}"

if [[ "${FOREGROUND}" == "true" ]]; then
  cd "${BACKEND_DIR}"
  exec "${PYTHON_CMD[@]}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
fi

write_runner() {
  local python_exe="$1"
  cat >"${RUNNER_FILE}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "${ROOT_DIR}"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi
cd "${BACKEND_DIR}"
exec "${python_exe}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" >>"${LOG_FILE}" 2>>"${ERR_LOG_FILE}"
EOF
  chmod +x "${RUNNER_FILE}"
}

start_with_launchd() {
  local python_exe="$1"
  write_runner "${python_exe}"
  cat >"${PLIST_FILE}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUNNER_FILE}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT_DIR}</string>
  <key>StandardOutPath</key>
  <string>${LOG_FILE}</string>
  <key>StandardErrorPath</key>
  <string>${ERR_LOG_FILE}</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF

  launchctl bootout "gui/$(id -u)" "${PLIST_FILE}" >/dev/null 2>&1 || true
  launchctl remove "${LAUNCHD_LABEL}" >/dev/null 2>&1 || true
  : >"${LOG_FILE}"
  : >"${ERR_LOG_FILE}"
  launchctl bootstrap "gui/$(id -u)" "${PLIST_FILE}"
  launchctl kickstart -k "gui/$(id -u)/${LAUNCHD_LABEL}" >/dev/null 2>&1 || true
}

start_with_nohup() {
  if [[ "${#PYTHON_CMD[@]}" -eq 1 && -x "${PYTHON_CMD[0]}" ]]; then
    write_runner "${PYTHON_CMD[0]}"
    nohup "${RUNNER_FILE}" >/dev/null 2>&1 &
  else
    (
      cd "${BACKEND_DIR}"
      exec nohup "${PYTHON_CMD[@]}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
    ) >>"${LOG_FILE}" 2>>"${ERR_LOG_FILE}" &
  fi
  printf '%s\n' "$!" >"${PID_FILE}"
}

start_with_screen() {
  local python_exe="$1"
  write_runner "${python_exe}"
  screen -S "${SCREEN_SESSION}" -X quit >/dev/null 2>&1 || true
  : >"${LOG_FILE}"
  : >"${ERR_LOG_FILE}"
  screen -dmS "${SCREEN_SESSION}" "${RUNNER_FILE}"
}

if command -v screen >/dev/null 2>&1 && [[ "${#PYTHON_CMD[@]}" -eq 1 && -x "${PYTHON_CMD[0]}" ]]; then
  start_with_screen "${PYTHON_CMD[0]}"
elif [[ "$(uname -s)" == "Darwin" && "${#PYTHON_CMD[@]}" -eq 1 && -x "${PYTHON_CMD[0]}" ]]; then
  start_with_launchd "${PYTHON_CMD[0]}"
else
  start_with_nohup
fi

PID=""
if [[ "${WAIT_FOR_HEALTH}" == "true" ]]; then
  if ! wait_for_backend_health "${HOST}" "${PORT}" 60; then
    log "BACKEND_SERVICE_START_FAILED"
    log "agent=${AGENT_NAME}"
    log "pid=${PID}"
    log "log=${LOG_FILE}"
    tail -n 80 "${LOG_FILE}" || true
    tail -n 80 "${ERR_LOG_FILE}" || true
    exit 1
  fi
fi

PID="$(port_owner_pid "${PORT}")"
if [[ -n "${PID}" ]]; then
  printf '%s\n' "${PID}" >"${PID_FILE}"
fi

log "BACKEND_SERVICE_READY"
log "agent=${AGENT_NAME}"
log "pid=${PID:-unknown}"
log "url=http://127.0.0.1:${PORT}"
log "health=http://127.0.0.1:${PORT}/api/v1/health/detail"
log "log=${LOG_FILE}"
