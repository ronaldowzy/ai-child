#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

env_true() {
  local value="${1:-}"
  case "$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

first_present_env_name() {
  for name in "$@"; do
    if [[ -n "${!name:-}" ]]; then
      printf '%s\n' "${name}"
      return 0
    fi
  done
  return 1
}

generate_fake_wav() {
  local target="$1"
  mkdir -p "$(dirname "${target}")"
  python3 - "${target}" <<'PY'
import math
import struct
import sys
import wave

path = sys.argv[1]
sample_rate = 16000
duration = 1.0
frequency = 440.0
with wave.open(path, "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)
    for index in range(int(sample_rate * duration)):
        value = int(0.15 * 32767 * math.sin(2 * math.pi * frequency * index / sample_rate))
        wav.writeframesraw(struct.pack("<h", value))
PY
}

provider="${CHILD_AI_ASR_PROVIDER:-${ASR_PROVIDER:-mock}}"
provider="$(printf '%s' "${provider}" | tr '[:upper:]' '[:lower:]')"
if [[ "${provider}" != "mimo" ]]; then
  echo "ASR_STATUS=mock_only"
  echo "reason=CHILD_AI_ASR_PROVIDER is not mimo"
  exit 0
fi

missing=()
env_true "${CHILD_AI_MIMO_ASR_ENABLED:-${MIMO_ASR_ENABLED:-}}" || missing+=("CHILD_AI_MIMO_ASR_ENABLED=true")
env_true "${CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO:-${MIMO_ASR_ALLOW_CHILD_AUDIO:-}}" || missing+=("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true")
env_true "${CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED:-${MIMO_ASR_RETENTION_POLICY_CHECKED:-}}" || missing+=("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true")
env_true "${CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED:-${MIMO_ASR_NO_TRAINING_CONFIRMED:-}}" || missing+=("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true")
if ! first_present_env_name CHILD_AI_MIMO_ASR_API_KEY CHILD_AI_MIMO_API_KEY CHILD_AI_MIMO_KEY >/dev/null; then
  missing+=("CHILD_AI_MIMO_ASR_API_KEY or CHILD_AI_MIMO_API_KEY")
fi

if ((${#missing[@]} > 0)); then
  echo "ASR_STATUS=policy_blocked"
  printf 'missing_env=%s\n' "$(IFS=,; printf '%s' "${missing[*]}")"
  exit 0
fi

audio_path="${CHILD_AI_ASR_SMOKE_WAV:-${MIMO_ASR_SMOKE_AUDIO:-}}"
if [[ -z "${audio_path}" ]]; then
  audio_path="${TMPDIR:-/tmp}/child-ai-asr-smoke/fake_asr_smoke_tone.wav"
  generate_fake_wav "${audio_path}"
  export CHILD_AI_ASR_SMOKE_WAV="${audio_path}"
  echo "ASR_STATUS=mimo_ready"
  echo "smoke_audio=synthetic_fake_wav"
  echo "note=synthetic audio validates provider request chain only, not Mandarin recognition accuracy"
else
  export CHILD_AI_ASR_SMOKE_WAV="${audio_path}"
  echo "ASR_STATUS=mimo_ready"
  echo "smoke_audio=provided_non_child_test_file"
fi

set +e
smoke_output="$(bash "${ROOT_DIR}/scripts/smoke_mimo_asr_opt_in.sh" 2>&1)"
smoke_status=$?
set -e
printf '%s\n' "${smoke_output}" | grep -E '^(provider|model|duration|confidence|errorCode)=' || true
if [[ "${smoke_status}" == "0" ]]; then
  echo "ASR_STATUS=mimo_smoke_pass"
  exit 0
fi

echo "ASR_STATUS=mimo_smoke_fail"
printf '%s\n' "${smoke_output}" | grep -E '^(ASR_SMOKE|error|reason|status)=' || true
exit 1
