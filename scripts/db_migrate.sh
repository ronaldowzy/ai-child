#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-child-ai}"
CONDA_CMD=""

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi

  if command -v conda >/dev/null 2>&1; then
    CONDA_CMD="$(command -v conda)"
  elif [[ -x "/opt/homebrew/bin/conda" ]]; then
    CONDA_CMD="/opt/homebrew/bin/conda"
  fi

  if [[ -n "${CONDA_CMD}" ]] && "${CONDA_CMD}" env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
    PYTHON_CMD=("${CONDA_CMD}" run --no-capture-output -n "${CONDA_ENV_NAME}" python)
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

  echo "No Python interpreter found. Set PYTHON_BIN or install/activate the ${CONDA_ENV_NAME} environment." >&2
  exit 1
}

TARGET_REVISION="${1:-head}"

resolve_python_cmd
cd "${BACKEND_DIR}"
echo "Running Alembic migrations to ${TARGET_REVISION}"
"${PYTHON_CMD[@]}" -m alembic -c alembic.ini upgrade "${TARGET_REVISION}"
