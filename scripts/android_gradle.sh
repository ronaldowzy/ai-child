#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="${ROOT_DIR}/android"

if [[ ! -d "${ANDROID_DIR}" ]]; then
  echo "android/ has not been initialized yet. Run S11 before Android Gradle tasks." >&2
  exit 1
fi

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

cd "${ANDROID_DIR}"
echo "Running Android Gradle with JAVA_HOME=${JAVA_HOME:-} ANDROID_HOME=${ANDROID_HOME:-}"
./gradlew "$@"
