#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "dev_backend.sh is a compatibility wrapper."
echo "Agent-managed backend services must use start/status/stop_backend_services.sh."
exec bash "${ROOT_DIR}/scripts/start_backend_services.sh" --foreground "$@"
