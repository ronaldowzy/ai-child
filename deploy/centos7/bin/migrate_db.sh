#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=backend_service_common.sh
source "${SCRIPT_DIR}/backend_service_common.sh"

ensure_runtime_dirs
load_service_env
resolve_python_bin

[[ -d "${BACKEND_DIR}" ]] || die "Backend directory not found: ${BACKEND_DIR}"

log "DB_MIGRATE: START"
log "app_root=${APP_ROOT}"
log "backend_dir=${BACKEND_DIR}"
log "env_file=${ENV_FILE}"
log "python=${PYTHON_BIN}"

cd "${BACKEND_DIR}"
"${PYTHON_BIN}" -m alembic -c alembic.ini upgrade head

log "DB_MIGRATE: PASS"
