# CODE_AGENT_TASK_12_SCOPE_REPAIR_AND_TASK11_QA_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: scope repair + Task 11 QA closeout  
Reason: Task 11 implementation mixed prompt/report reset with an unrelated TTS provider feature.

---

## 0. Situation

Task 11 was intentionally narrow:

```text
1. replace child conversation prompt files with supplied text;
2. replace parent report prompt with supplied text;
3. improve parent report payload with short_content_hint;
4. update parent report UI copy;
5. add tests.
```

However, the implementation branch also added unrelated TTS work:

```text
1. sherpa-onnx local TTS provider;
2. new TTS config/env fields;
3. TtsService fallback behavior changes;
4. TTS data policy changes;
5. new wav asset;
6. backend README / voice design TTS provider docs.
```

This violates Task 11 constraints:

```text
Do not modify TTS provider, ASR, image upload, auth/account, DB migration, navigation, or new feature entry.
```

Task 12 must first restore scope discipline.

---

## 1. Goal

Keep the valid Task 11 prompt/report changes. Remove or revert unrelated TTS provider changes from main.

After repair, main should contain:

```text
YES:
- Prompt reset files.
- Parent report prompt reset.
- Parent report short_content_hint payload.
- Parent report UI copy changes.
- Related tests.
- Code agent context/workflow docs.

NO:
- sherpa-onnx provider.
- new local TTS fallback logic.
- new TTS env/config knobs.
- new voice wav asset.
- TTS service fallback behavior changes.
- TTS docs claiming local fallback was added.
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

---

## 3. Allowed files

Allowed to modify only for reverting the unrelated TTS changes and final QA docs:

```text
.env.example
backend/app/core/config.py
backend/app/domain/tts.py
backend/app/providers/tts/sherpa_onnx_provider.py
backend/app/services/tts_data_policy_guard.py
backend/app/services/tts_service.py
backend/assets/voices/xiaobaohu_voice_v01_short.wav
backend/README.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Also allowed to adjust tests only if they were added for the unrelated TTS change.

Do not touch Task 11 prompt/report files unless a test proves a regression.

---

## 4. Required repair

### 4.1 Remove sherpa-onnx provider feature

Revert/delete:

```text
backend/app/providers/tts/sherpa_onnx_provider.py
backend/assets/voices/xiaobaohu_voice_v01_short.wav
```

Remove config/env entries added only for sherpa/local TTS.

Remove any provider registry hook or fallback path that automatically falls back to sherpa-onnx.

### 4.2 Restore TTS policy

The product rule remains:

```text
1. MiMo VoiceClone remote audio_url is the Xiaobaihu voice path.
2. Android must not use system TTS as automatic child-facing fallback.
3. No new TTS provider is introduced in Task 11/12.
4. If TTS fails, text remains visible and child can continue; no voice mixing.
```

### 4.3 Keep Task 11 changes

Do not revert:

```text
backend/app/prompts/global_system_v0_1.txt
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
backend/app/services/parent_report_service.py
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
Task 11 tests
```

unless there is an objective test or compilation issue.

---

## 5. Tests

Run at minimum:

```bash
cd backend && pytest backend/app/tests/test_parent_report_service.py backend/app/tests/test_parent_report_conversation_analysis.py backend/app/tests/test_prompt_manager.py
cd backend && pytest backend/app/tests/test_tts_service.py backend/app/tests/test_tts_data_policy_guard.py || true
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
3. which unrelated TTS files/logic were removed;
4. confirmation that Task 11 prompt/report changes remain;
5. test commands and exact results;
6. confirmation no auth/account/ASR/image/upload/navigation code was touched;
7. remaining QA items for tonight's APK test.
```

---

## 7. Important

This task is a process correction. Do not add another new feature while fixing scope drift.

If you believe the local TTS provider is valuable, document it as a future proposal in a separate design note only after Task 12 is complete. Do not keep it in this branch.
