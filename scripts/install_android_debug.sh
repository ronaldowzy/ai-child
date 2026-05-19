#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK_PATH="${ROOT_DIR}/android/app/build/outputs/apk/debug/app-debug.apk"

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

if ! adb devices | awk 'NR > 1 && $2 == "device" {found=1} END {exit found ? 0 : 1}'; then
  echo "No Android device or emulator is connected." >&2
  echo "Start one with: bash scripts/start_android_emulator.sh" >&2
  exit 1
fi

bash "${ROOT_DIR}/scripts/android_gradle.sh" assembleDebug

echo "Installing ${APK_PATH}"
adb install -r "${APK_PATH}"
adb shell am start -n com.childai.companion/.MainActivity
