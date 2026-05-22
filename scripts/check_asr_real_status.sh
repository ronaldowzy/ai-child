#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PORT="${ASR_STATUS_PORT:-18092}"
BASE_URL="${ASR_SMOKE_BASE_URL:-http://127.0.0.1:${PORT}}"
START_SERVER="${ASR_STATUS_START_SERVER:-true}"
SERVER_PID=""

env_true() {
  local value="${1:-}"
  case "$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

load_dotenv() {
  if [[ "${ASR_STATUS_LOAD_DOTENV:-true}" != "true" ]]; then
    echo "dotenv_loaded=false"
    return
  fi
  if [[ ! -f "${ROOT_DIR}/.env" ]]; then
    echo "dotenv_loaded=false"
    return
  fi

  set -a
  set +u
  # shellcheck source=/dev/null
  . "${ROOT_DIR}/.env"
  set -u
  set +a
  echo "dotenv_loaded=true"
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

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi
  if command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if [[ -x "/opt/homebrew/bin/conda" ]] && /opt/homebrew/bin/conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(/opt/homebrew/bin/conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  echo "No Python interpreter found. Set PYTHON_BIN." >&2
  exit 1
}

generate_fake_wav() {
  local target="$1"
  mkdir -p "$(dirname "${target}")"
  "${PYTHON_CMD[@]}" - "${target}" <<'PY'
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

safe_audio_path() {
  local provided_path="${CHILD_AI_ASR_SMOKE_WAV:-${MIMO_ASR_SMOKE_AUDIO:-}}"
  local lower_name
  if [[ -n "${provided_path}" ]]; then
    lower_name="$(basename "${provided_path}" | tr '[:upper:]' '[:lower:]')"
    case "${lower_name}" in
      *fake*|*smoke*|*test*|*fixture*|*sample*)
        if [[ -f "${provided_path}" ]]; then
          printf '%s\n' "${provided_path}"
          return
        fi
        echo "provided_audio_ignored=file_not_found"
        ;;
      *)
        echo "provided_audio_ignored=filename_missing_fake_marker"
        ;;
    esac
  fi

  local generated_path="${TMPDIR:-/tmp}/child-ai-asr-smoke/fake_asr_smoke_tone.wav"
  generate_fake_wav "${generated_path}"
  printf '%s\n' "${generated_path}"
}

wait_for_health() {
  local url="${BASE_URL%/}/api/v1/health"
  for _ in $(seq 1 100); do
    if curl --noproxy '*' -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "ASR_STATUS=mimo_smoke_fail"
  echo "reason=temporary_backend_not_healthy"
  return 1
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

start_backend_if_needed() {
  if [[ "${START_SERVER}" != "true" ]]; then
    wait_for_health
    return
  fi

  (
    cd "${BACKEND_DIR}"
    "${PYTHON_CMD[@]}" -m uvicorn app.main:app \
      --host 127.0.0.1 \
      --port "${PORT}" \
      --log-level warning
  ) &
  SERVER_PID="$!"
  wait_for_health
}

load_dotenv
resolve_python_cmd

original_provider="${CHILD_AI_ASR_PROVIDER:-${ASR_PROVIDER:-mock}}"
key_source=""
if key_source="$(first_present_env_name CHILD_AI_MIMO_ASR_API_KEY CHILD_AI_MIMO_API_KEY CHILD_AI_MIMO_KEY CHILD_AI_MIMO_TTS_API_KEY)"; then
  echo "mimo_key_present=true"
  echo "mimo_key_source=${key_source}"
else
  echo "mimo_key_present=false"
  echo "ASR_STATUS=policy_blocked"
  echo "reason=missing_mimo_key"
  exit 2
fi

if [[ -z "${CHILD_AI_MIMO_ASR_API_KEY:-}" && -n "${CHILD_AI_MIMO_KEY:-}" ]]; then
  export CHILD_AI_MIMO_ASR_API_KEY="${CHILD_AI_MIMO_KEY}"
fi
if [[ -z "${CHILD_AI_MIMO_API_KEY:-}" && -n "${CHILD_AI_MIMO_KEY:-}" ]]; then
  export CHILD_AI_MIMO_API_KEY="${CHILD_AI_MIMO_KEY}"
fi

export CHILD_AI_ASR_PROVIDER="mimo"
export CHILD_AI_MIMO_ASR_ENABLED="true"
export CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO="true"
export CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED="true"
export CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED="true"

audio_path="$(safe_audio_path | tail -n 1)"
export CHILD_AI_ASR_SMOKE_WAV="${audio_path}"

echo "asr_code_implemented=yes"
echo "initial_asr_provider=${original_provider}"
echo "smoke_env_overlay=applied"
if [[ "$(basename "${audio_path}")" == "fake_asr_smoke_tone.wav" ]]; then
  echo "smoke_audio=synthetic_fake_wav"
  echo "note=synthetic audio validates provider request chain only, not Mandarin recognition accuracy"
else
  echo "smoke_audio=provided_non_child_test_file"
fi
echo "ASR_STATUS=mimo_ready"

start_backend_if_needed

set +e
smoke_output="$(
  ASR_SMOKE_BASE_URL="${BASE_URL}" \
    bash "${ROOT_DIR}/scripts/smoke_mimo_asr_opt_in.sh" 2>&1
)"
smoke_status=$?
set -e

printf '%s\n' "${smoke_output}" | grep -E '^(status|provider|model|duration|confidence|errorCode)=' || true
if [[ "${smoke_status}" == "0" ]]; then
  echo "ASR_STATUS=mimo_smoke_pass"
  exit 0
fi

echo "ASR_STATUS=mimo_smoke_fail"
printf '%s\n' "${smoke_output}" | grep -E '^(ASR_SMOKE|error|reason|status|provider|model|duration|confidence|errorCode)=' || true
exit 1
