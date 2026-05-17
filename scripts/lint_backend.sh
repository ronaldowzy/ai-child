#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "backend/ has not been initialized yet. Run S01 backend skeleton before backend linting." >&2
  exit 1
fi

cd "${BACKEND_DIR}"
python -m ruff check . "$@"
