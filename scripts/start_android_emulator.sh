#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AVD_NAME="${AVD_NAME:-child_ai_tablet_api35}"
MODE="${1:-window}"

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

if ! avdmanager list avd | grep -q "Name: ${AVD_NAME}$"; then
  echo "AVD ${AVD_NAME} does not exist." >&2
  echo "Install emulator image and create it with:" >&2
  echo "  yes | bash scripts/android_env.sh sdkmanager --install \"emulator\" \"system-images;android-35;google_apis_tablet;arm64-v8a\"" >&2
  echo "  printf 'no\\n' | bash scripts/android_env.sh avdmanager create avd -n ${AVD_NAME} -k \"system-images;android-35;google_apis_tablet;arm64-v8a\" --device \"pixel_tablet\"" >&2
  exit 1
fi

ARGS=(-avd "${AVD_NAME}" -no-snapshot -no-boot-anim)

case "${MODE}" in
  --headless)
    ARGS+=(-no-window -no-audio -gpu swiftshader_indirect)
    ;;
  window|--window)
    ;;
  *)
    echo "Usage: bash scripts/start_android_emulator.sh [--headless|--window]" >&2
    exit 1
    ;;
esac

echo "Starting Android emulator ${AVD_NAME} (${MODE})"
exec emulator "${ARGS[@]}"
