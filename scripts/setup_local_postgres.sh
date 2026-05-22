#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.local.yml"
DATABASE_URL="${CHILD_AI_DATABASE_URL:-postgresql+psycopg://child_ai:child_ai@localhost:5432/child_ai_dev}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-child-ai-postgres-local}"

log() {
  printf '%s\n' "$*"
}

run_migrate_and_smoke() {
  export CHILD_AI_DATABASE_URL="${DATABASE_URL}"
  if ! bash "${ROOT_DIR}/scripts/db_migrate.sh"; then
    return 1
  fi
  if ! bash "${ROOT_DIR}/scripts/smoke_db_persistence.sh"; then
    return 1
  fi
}

wait_for_docker_postgres() {
  for _ in $(seq 1 80); do
    local health_status
    health_status="$(docker inspect -f '{{.State.Health.Status}}' "${POSTGRES_CONTAINER}" 2>/dev/null || true)"
    if [[ "${health_status}" == "healthy" ]]; then
      return 0
    fi
    if docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U child_ai -d child_ai_dev >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

try_docker_setup() {
  if ! command -v docker >/dev/null 2>&1; then
    log "Docker CLI not found; trying Homebrew PostgreSQL fallback."
    return 2
  fi
  if ! docker info >/dev/null 2>&1; then
    log "Docker CLI exists but daemon is not reachable; trying Homebrew PostgreSQL fallback."
    return 2
  fi
  if ! docker compose version >/dev/null 2>&1; then
    log "Docker Compose plugin is not available; trying Homebrew PostgreSQL fallback."
    return 2
  fi

  log "Starting local PostgreSQL with Docker Compose..."
  if ! docker compose -f "${COMPOSE_FILE}" up -d postgres; then
    log "Docker Compose failed to start postgres; trying Homebrew PostgreSQL fallback."
    return 2
  fi
  if ! wait_for_docker_postgres; then
    log "Docker PostgreSQL did not become ready."
    return 1
  fi
  if ! run_migrate_and_smoke; then
    log "POSTGRES_SETUP: FAIL"
    log "reason=migration_or_db_smoke_failed"
    return 1
  fi
  log "POSTGRES_SETUP: PASS"
  return 0
}

brew_postgres_bin() {
  local prefix
  prefix="$(brew --prefix postgresql@16 2>/dev/null || true)"
  if [[ -n "${prefix}" && -x "${prefix}/bin/psql" ]]; then
    printf '%s\n' "${prefix}/bin"
    return 0
  fi
  return 1
}

wait_for_brew_postgres() {
  local pg_bin="$1"
  for _ in $(seq 1 80); do
    if "${pg_bin}/pg_isready" -d postgres >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

try_brew_setup() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=not_macos_and_docker_unavailable"
    return 2
  fi
  if ! command -v brew >/dev/null 2>&1; then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=docker_unavailable_and_brew_not_found"
    return 2
  fi

  if ! brew list postgresql@16 >/dev/null 2>&1; then
    log "Installing postgresql@16 with Homebrew..."
    if ! brew install postgresql@16; then
      log "POSTGRES_SETUP: BLOCKED"
      log "reason=brew_install_postgresql16_failed"
      return 2
    fi
  fi

  local pg_bin
  if ! pg_bin="$(brew_postgres_bin)"; then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=postgresql16_psql_not_found_after_install"
    return 2
  fi

  log "Starting postgresql@16 with Homebrew services..."
  if ! brew services start postgresql@16 >/dev/null 2>&1; then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=brew_services_start_postgresql16_failed"
    return 2
  fi
  if ! wait_for_brew_postgres "${pg_bin}"; then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=homebrew_postgres_not_ready"
    return 2
  fi

  log "Ensuring local child_ai role and child_ai_dev database exist..."
  if ! "${pg_bin}/psql" -v ON_ERROR_STOP=1 -d postgres <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'child_ai') THEN
    CREATE ROLE child_ai WITH LOGIN PASSWORD 'child_ai';
  END IF;
END
$$;
ALTER ROLE child_ai WITH LOGIN PASSWORD 'child_ai';
SQL
  then
    log "POSTGRES_SETUP: BLOCKED"
    log "reason=postgres_role_setup_failed"
    return 2
  fi

  local db_exists
  db_exists="$("${pg_bin}/psql" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'child_ai_dev'" || true)"
  if [[ "${db_exists//[[:space:]]/}" != "1" ]]; then
    if ! "${pg_bin}/createdb" -O child_ai child_ai_dev; then
      log "POSTGRES_SETUP: BLOCKED"
      log "reason=postgres_database_create_failed"
      return 2
    fi
  fi

  if ! run_migrate_and_smoke; then
    log "POSTGRES_SETUP: FAIL"
    log "reason=migration_or_db_smoke_failed"
    return 1
  fi
  log "POSTGRES_SETUP: PASS"
  return 0
}

main() {
  local docker_status=0
  try_docker_setup || docker_status=$?
  if [[ "${docker_status}" == "0" ]]; then
    return 0
  fi
  if [[ "${docker_status}" == "1" ]]; then
    log "POSTGRES_SETUP: FAIL"
    log "reason=docker_postgres_setup_failed"
    return 1
  fi

  local brew_status=0
  try_brew_setup || brew_status=$?
  if [[ "${brew_status}" == "0" ]]; then
    return 0
  fi
  return "${brew_status}"
}

main "$@"
