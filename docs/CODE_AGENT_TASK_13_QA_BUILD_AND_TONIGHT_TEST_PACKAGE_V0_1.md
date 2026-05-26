# CODE_AGENT_TASK_13_QA_BUILD_AND_TONIGHT_TEST_PACKAGE_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: QA build package only  
Goal: create a stable APK/backend test package for tonight's real-device test.

---

## 0. Important

Do not add new product features in Task 13.

Do not change prompts, auth, ASR, image upload, parent report logic, TTS provider logic, database migrations, or Android navigation unless a build/test failure proves a tiny fix is necessary.

Task 13 is only for:

```text
1. verify current main builds;
2. produce an APK;
3. document exact backend config for MiMo VoiceClone path;
4. document exact backend config for sherpa-onnx local TTS experiment path;
5. update QA checklist with tonight's focused scenarios;
6. report any blockers clearly.
```

---

## 1. Required reading

```text
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
docs/CODE_AGENT_TASK_12_SCOPE_REPAIR_AND_TASK11_QA_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
backend/README.md
android/README.md
```

---

## 2. Required commands

Run and report exact result:

```bash
cd backend && pytest backend/app/tests/test_parent_report_service.py backend/app/tests/test_parent_report_conversation_analysis.py backend/app/tests/test_prompt_manager.py
cd backend && pytest backend/app/tests/test_tts_service.py backend/app/tests/test_tts_data_policy_guard.py
cd backend && ruff check .
cd android && ./gradlew test
cd android && ./gradlew assembleDebug
shasum -a 256 android/app/build/outputs/apk/debug/app-debug.apk
```

If any command fails, do not hide it. Report exact failure and only make the smallest required fix.

---

## 3. Backend config package for tonight

Document two backend modes.

### Mode A: MiMo VoiceClone primary, no local fallback

Use this to validate Task 11 prompt/report quality without TTS provider change noise.

```bash
CHILD_AI_TTS_PROVIDER=mimo
CHILD_AI_TTS_ENABLE_LOCAL_FALLBACK=false
CHILD_AI_SHERPA_ONNX_TTS_ENABLED=false
```

Expected:

```text
1. Xiaobaihu voice uses MiMo VoiceClone remote audio.
2. No sherpa fallback happens.
3. If MiMo TTS fails, text remains visible; no Android system TTS mixing.
```

### Mode B: MiMo primary + sherpa-onnx local fallback enabled

Use this only after Mode A sanity pass.

```bash
CHILD_AI_TTS_PROVIDER=mimo
CHILD_AI_TTS_ENABLE_LOCAL_FALLBACK=true
CHILD_AI_SHERPA_ONNX_TTS_ENABLED=true
CHILD_AI_TTS_FALLBACK_PROVIDER=sherpa_onnx
```

Expected:

```text
1. MiMo remains primary.
2. sherpa fallback only happens for transient remote/provider/data-policy failures.
3. config errors still propagate and are not hidden.
4. logs show actual provider used.
```

### Optional Mode C: sherpa-onnx primary local-only experiment

Use only if the product owner explicitly wants to compare local voice quality/latency.

```bash
CHILD_AI_TTS_PROVIDER=sherpa_onnx
CHILD_AI_SHERPA_ONNX_TTS_ENABLED=true
```

Expected:

```text
1. All TTS uses local sherpa-onnx.
2. Voice quality must be judged on device.
3. This is not the default product path.
```

---

## 4. Tonight's focused real-device QA

Do not try to test everything. Focus on visible impact.

### A. Task 11 conversation quality

Test with a synthetic/low-private conversation:

```text
1. child says they were nervous before a match/competition;
2. child gives a short answer after 2-3 turns;
3. child uploads or talks about an object/photo;
4. child says they need to do English check-in / homework / go away for a bit;
5. child says “一会再聊” or “不聊了”.
```

Expected:

```text
1. Xiaobaihu uses short child-friendly replies.
2. Xiaobaihu does not keep interviewing.
3. Xiaobaihu respects stop/leave signals.
4. Xiaobaihu does not sound like teacher/customer-service/product manual.
```

### B. Parent report readability

Generate parent report after the above flow.

Expected:

```text
1. Section title says “今晚可以这样聊”, not “接一句”.
2. Section title says “今天聊了什么”.
3. Report explains at a high level: match/competition, image/object, English check-in or leaving.
4. No raw transcript.
5. No internal words: 接一句, 桥接, 结构化摘要, 表达入口.
6. Parent can understand what happened and what to say tonight.
```

### C. TTS comparison

Run Mode A first. If Mode A works, optionally run Mode B or C.

Record for each mode:

```text
1. first voice latency;
2. voice quality;
3. whether Xiaobaihu identity feels consistent;
4. whether there are glitches, cutoffs, wrong pronunciation, or robotic artifacts;
5. request_id and provider used if available.
```

Do not judge prompt/report quality and TTS provider quality in the same sentence. Keep them separate.

---

## 5. Final response required

Report:

```text
1. commit sha;
2. exact commands run and results;
3. APK path, size, SHA256;
4. backend base URL to use tonight;
5. Mode A/B/C config notes;
6. any build/test failures and fixes;
7. confirmation no new features were added;
8. final tonight QA checklist summary.
```
