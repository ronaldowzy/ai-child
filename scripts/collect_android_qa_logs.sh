#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(TZ=UTC date '+%Y%m%dT%H%M%SZ')"
OUTPUT_DIR="${ROOT_DIR}/qa_logs/${TIMESTAMP}"

# shellcheck source=scripts/android_env.sh
source "${ROOT_DIR}/scripts/android_env.sh"

if ! command -v adb >/dev/null 2>&1; then
  echo "ANDROID_QA_LOGS: SKIP"
  echo "reason=adb_not_found"
  echo "hint=Install Android SDK platform-tools or set CHILD_AI_ANDROID_HOME."
  exit 0
fi

mkdir -p "${OUTPUT_DIR}"

adb devices > "${OUTPUT_DIR}/adb_devices.txt" 2>&1 || true
{
  adb logcat -d 2>&1 || true
} | grep -E 'childai|ChildAi|XiaoBaiHu|xiaobaohu|Conversation|ASR|TTS|FoxAgent|AudioSegment|Opening' \
  > "${OUTPUT_DIR}/app_logcat_filtered.txt" || true

cat > "${OUTPUT_DIR}/README.txt" <<EOF
Android QA logs collected at ${TIMESTAMP}.

Files:
- adb_devices.txt
- app_logcat_filtered.txt

Boundary:
- This script only collects adb device listing and filtered app logcat text.
- It does not collect child audio, photos, screenshots, MiMo keys, or APK files.
EOF

echo "ANDROID_QA_LOGS: PASS"
echo "output_dir=${OUTPUT_DIR}"
