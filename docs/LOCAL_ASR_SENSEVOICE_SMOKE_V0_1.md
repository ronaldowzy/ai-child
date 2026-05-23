# Local SenseVoice ASR Smoke V0.1

> Local ASR smoke summary. This is not real child accuracy validation, not Android device QA, and not a production data policy.

## Run Metadata

- Executed at: `2026-05-23T17:22:38+08:00`
- Commit: `40456d8`
- Status: `PASS`
- Reason: `none`
- Provider under test: `local_sensevoice`
- Fallback provider: `mock`
- Elapsed ms: `1067.2`

## Environment Checks

- numpy import: `present`
- sherpa_onnx import: `present`
- model.int8.onnx: `present`
- tokens.txt: `present`
- model path: `backend/models/asr/sensevoice/model.int8.onnx`
- tokens path: `backend/models/asr/sensevoice/tokens.txt`

## Audio Boundary

- audio source: `user_non_child_wav`
- audio path: `child-ai-local-sensevoice-non-child-smoke.wav`
- audio file committed: `no`
- raw audio/base64 in report: `no`
- real child audio used: `no`

## Provider Result

- provider result: `local_sensevoice`
- model: `model.int8.onnx`
- transcript status: `ok`
- transcript chars: `17`
- confidence: `none`
- duration ms: `3373`
- fallback used: `false`
- local primary failed: `false`
- error type: `none`
- error code: `none`

## Notes

- none

## Interpretation

- `PASS` means local dependencies and model files were present and the response provider was `local_sensevoice` with a stable API status.
- `BLOCKED` means the local primary path could not be verified, or only a fallback provider responded.
- `FAIL` means an unexpected provider/API failure occurred.
- A silent generated WAV only verifies the request/init path; it does not validate Chinese recognition accuracy.
- Real child speech accuracy and Redmi K60 / Honor Pad 5 Android QA remain separate manual validation items.
