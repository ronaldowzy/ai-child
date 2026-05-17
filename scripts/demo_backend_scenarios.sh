#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "backend/ has not been initialized yet. Run S01 backend skeleton before demo scenarios." >&2
  exit 1
fi

echo "Backend demo scenarios are not available until the conversation API is implemented."
echo "Expected later flow: health check, after-school check-in, learning help, bedtime reflection, safety risk."
exit 1
