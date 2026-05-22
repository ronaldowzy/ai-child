#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export CHILD_AI_ASR_PROVIDER="${CHILD_AI_ASR_PROVIDER:-${ASR_PROVIDER:-}}"
export CHILD_AI_MIMO_ASR_ENABLED="${CHILD_AI_MIMO_ASR_ENABLED:-${MIMO_ASR_ENABLED:-}}"
export CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO="${CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO:-${MIMO_ASR_ALLOW_CHILD_AUDIO:-}}"
export CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED="${CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED:-${MIMO_ASR_RETENTION_POLICY_CHECKED:-}}"
export CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED="${CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED:-${MIMO_ASR_NO_TRAINING_CONFIRMED:-}}"
export CHILD_AI_ASR_SMOKE_WAV="${CHILD_AI_ASR_SMOKE_WAV:-${MIMO_ASR_SMOKE_AUDIO:-}}"

if [[ -z "${CHILD_AI_MIMO_ASR_API_KEY:-}" && -n "${CHILD_AI_MIMO_KEY:-}" ]]; then
  export CHILD_AI_MIMO_ASR_API_KEY="${CHILD_AI_MIMO_KEY}"
fi
if [[ -z "${CHILD_AI_MIMO_API_KEY:-}" && -n "${CHILD_AI_MIMO_KEY:-}" ]]; then
  export CHILD_AI_MIMO_API_KEY="${CHILD_AI_MIMO_KEY}"
fi

cat <<'INFO'
MiMo ASR opt-in smoke will only run when all policy env values are explicit.
It must use a developer-provided non-child fake/smoke/test audio file.
This script never prints API keys, audio base64, transcript text, or raw provider response.
INFO

exec bash "${ROOT_DIR}/scripts/smoke_mimo_asr.sh"
