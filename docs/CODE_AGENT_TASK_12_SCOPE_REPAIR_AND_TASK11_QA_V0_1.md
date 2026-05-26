# CODE_AGENT_TASK_12_SCOPE_REPAIR_AND_TASK11_QA_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: scope clarification + Task 11 QA closeout + authorized TTS experiment containment  
Reason: Task 11 implementation landed valid prompt/report reset changes and also included a separate local TTS experiment that the product owner had authorized outside Task 11.

---

## 0. Updated situation

Task 11 was intentionally narrow:

```text
1. replace child conversation prompt files with supplied text;
2. replace parent report prompt with supplied text;
3. improve parent report payload with short_content_hint;
4. update parent report UI copy;
5. add tests.
```

The implementation also included local TTS work:

```text
1. sherpa-onnx local TTS provider;
2. new TTS config/env fields;
3. TtsService fallback behavior changes;
4. TTS data policy changes;
5. new wav asset;
6. backend README / voice design TTS provider docs.
```

Master review initially treated this as scope drift. The product owner clarified that this TTS work was separately requested and locally tested the night before. Therefore **do not roll it back**.

Task 12 must now do two things:

```text
1. Preserve Task 11 prompt/report changes.
2. Preserve the authorized local TTS work, but isolate it as an experimental, feature-flagged, documented path with tests and QA rows.
```

Do not add further TTS functionality beyond containment and validation.

---

## 1. Goal

After Task 12, main should be clear and testable:

```text
YES:
- Task 11 prompt reset files remain.
- Task 11 parent report prompt reset remains.
- Parent report short_content_hint payload remains.
- Parent report UI copy changes remain.
- Local sherpa-onnx TTS provider remains, because product owner authorized it.
- Local TTS path is documented as experimental / family-beta only.
- Local TTS path is feature-flagged or config-gated.
- MiMo VoiceClone remains the primary Xiaobaihu voice path unless config explicitly enables/chooses local TTS fallback.
- No Android system TTS auto-mixing is reintroduced.
- Tests cover the TTS fallback/config behavior and data policy.

NO:
- Do not delete Task 11 prompt/report changes.
- Do not delete the authorized local TTS provider.
- Do not make local TTS silently override MiMo in all environments.
- Do not claim the local TTS voice is final production voice.
- Do not add more new providers or UI features.
```

---

## 2. Required reading

Before coding, read:

```text
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
backend/README.md
```

Also inspect current TTS changes:

```text
.env.example
backend/app/core/config.py
backend/app/domain/tts.py
backend/app/providers/tts/sherpa_onnx_provider.py
backend/app/services/tts_data_policy_guard.py
backend/app/services/tts_service.py
backend/assets/voices/xiaobaohu_voice_v01_short.wav
```

---

## 3. Allowed files

Allowed to modify only for TTS containment/validation and Task 11 QA docs:

```text
.env.example
backend/app/core/config.py
backend/app/domain/tts.py
backend/app/providers/tts/sherpa_onnx_provider.py
backend/app/services/tts_data_policy_guard.py
backend/app/services/tts_service.py
backend/app/tests/test_tts_service.py
backend/app/tests/test_tts_data_policy_guard.py
backend/README.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Allowed to inspect but avoid modifying unless a test proves a regression:

```text
backend/app/prompts/global_system_v0_1.txt
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
backend/app/services/parent_report_service.py
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
Task 11 tests
```

Forbidden unless explicitly necessary to fix a compile/test failure:

```text
auth/account code
ASR code
image upload code
Android navigation
new UI entry points
new database migrations
```

---

## 4. Required work

### 4.1 Preserve and label local TTS as experimental

Keep:

```text
backend/app/providers/tts/sherpa_onnx_provider.py
backend/assets/voices/xiaobaohu_voice_v01_short.wav
```

But ensure docs/config make its status clear:

```text
1. local sherpa-onnx TTS is family-beta experimental;
2. MiMo VoiceClone remains the preferred/primary remote Xiaobaihu voice path;
3. local TTS is for latency/fallback comparison and must be explicitly enabled/configured;
4. local TTS voice quality and child acceptance require real-device QA;
5. this does not reintroduce Android system TTS fallback.
```

### 4.2 Config-gate fallback behavior

Verify or implement a config gate so local TTS does not unexpectedly override the primary provider.

Acceptable behavior:

```text
TTS_PROVIDER=mimo_voiceclone
TTS_FALLBACK_PROVIDER=sherpa_onnx   # optional, explicit
TTS_ENABLE_LOCAL_FALLBACK=true      # or equivalent explicit flag
```

Exact env names may differ, but must satisfy:

```text
1. default behavior is documented;
2. fallback behavior is explicit;
3. config/provider errors do not silently mask broken production config unless intentionally marked transient;
4. transient remote provider failures may fall back only if local fallback is enabled;
5. logs/metadata show which provider produced the audio.
```

### 4.3 Preserve Task 11 prompt/report changes

Confirm these remain present:

```text
backend/app/prompts/global_system_v0_1.txt
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
backend/app/services/parent_report_service.py
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
```

Do not rewrite prompts again in Task 12 unless a test proves accidental corruption.

### 4.4 Add/verify tests

Add or verify tests for:

```text
1. local fallback is not used unless config enables it;
2. MiMo/provider config errors are not silently hidden as local fallback success;
3. transient remote TTS errors can use local fallback only when enabled;
4. `TtsDataPolicyGuard` treats local sherpa-onnx as local-only and does not send child text to external service;
5. metadata or result provider name identifies sherpa_onnx vs mimo_voiceclone;
6. Task 11 parent report title tests still pass;
7. Task 11 parent report prompt/payload tests still pass.
```

### 4.5 QA docs

Update QA checklist with explicit real-device rows:

```text
1. MiMo VoiceClone path: baseline voice quality/latency.
2. sherpa-onnx local TTS path: latency, voice quality, child acceptance.
3. fallback path: remote transient failure -> local fallback only if enabled.
4. no Android system TTS mixing.
5. opening first voice latency with provider used.
```

Do not mark PASS unless actually tested on device.

---

## 5. Tests

Run at minimum:

```bash
cd backend && pytest backend/app/tests/test_parent_report_service.py backend/app/tests/test_parent_report_conversation_analysis.py backend/app/tests/test_prompt_manager.py
cd backend && pytest backend/app/tests/test_tts_service.py backend/app/tests/test_tts_data_policy_guard.py
cd backend && ruff check .
cd android && ./gradlew test
```

If a test file does not exist, say so. Do not hide skipped tests.

---

## 6. Final response required

Report:

```text
1. commit sha;
2. exact files changed;
3. confirmation that Task 11 prompt/report changes remain;
4. confirmation that local sherpa-onnx TTS was preserved, not rolled back;
5. config flags/env names controlling local TTS/fallback;
6. which provider is default and when fallback happens;
7. TTS tests and parent-report tests run with exact results;
8. confirmation no auth/account/ASR/image/upload/navigation code was touched;
9. remaining QA items for tonight's APK test, especially local TTS voice quality and latency.
```

---

## 7. Important

This task is a containment and validation task. Do not add another new feature while doing it.

If further local TTS quality tuning is needed, propose it as a separate future task after real-device QA. Do not do broad tuning in Task 12.
