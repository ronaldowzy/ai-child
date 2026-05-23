#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK_PATH="${ROOT_DIR}/android/app/build/outputs/apk/debug/app-debug.apk"

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

if ! adb devices | awk 'NR > 1 && $2 == "device" {found=1} END {exit found ? 0 : 1}'; then
  echo "No physical Android device is connected." >&2
  echo "Connect Redmi K60 or Honor Pad 5 with USB debugging enabled." >&2
  exit 1
fi

bash "${ROOT_DIR}/scripts/build_device_debug_apk.sh" --base-url "http://192.168.0.118:8000/"

echo "Installing ${APK_PATH}"
adb install -r "${APK_PATH}"
adb shell am start -n com.childai.companion/.MainActivity
