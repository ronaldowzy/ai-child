#!/usr/bin/env bash
set -euo pipefail

DEFAULT_JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
DEFAULT_ANDROID_HOME="${HOME}/Library/Android/sdk"

if [[ -d "${DEFAULT_JAVA_HOME}" ]]; then
  export JAVA_HOME="${CHILD_AI_JAVA_HOME:-${DEFAULT_JAVA_HOME}}"
fi

if [[ -d "${DEFAULT_ANDROID_HOME}" ]]; then
  export ANDROID_HOME="${CHILD_AI_ANDROID_HOME:-${ANDROID_HOME:-${DEFAULT_ANDROID_HOME}}}"
  export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME}}"
fi

if [[ -n "${JAVA_HOME:-}" ]]; then
  export PATH="${JAVA_HOME}/bin:${PATH}"
fi

if [[ -n "${ANDROID_HOME:-}" ]]; then
  export PATH="${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${PATH}"
fi

# When sourced by another bash script, only export variables.
if (return 0 2>/dev/null); then
  return 0
fi

if [[ $# -gt 0 ]]; then
  exec "$@"
fi

echo "JAVA_HOME=${JAVA_HOME:-}"
echo "ANDROID_HOME=${ANDROID_HOME:-}"
echo "ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT:-}"

if command -v java >/dev/null 2>&1; then
  java -version
else
  echo "java is not available on PATH after loading android_env.sh" >&2
  exit 1
fi

if command -v adb >/dev/null 2>&1; then
  adb version | head -n 1
else
  echo "adb is not available on PATH after loading android_env.sh" >&2
  exit 1
fi
