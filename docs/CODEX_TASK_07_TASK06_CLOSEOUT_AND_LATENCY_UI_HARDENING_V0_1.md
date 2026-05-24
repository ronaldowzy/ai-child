# Codex Task 07: Task 06 Closeout and Latency/UI Hardening v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: closeout after Task 06 post-device QA product refinement  
Recommended mode: four lanes on separate branches/worktrees; if only one Codex session is available, execute A -> B -> C -> D.

---

## 0. Why this task

Task 06 implemented the right product direction:

```text
1. Parent settings now emphasize child profile instead of visible hard time periods.
2. Turn guidance can detect low engagement / repeated same-topic turns and recommend topic shift.
3. Static curated topic seeds exist.
4. Father report now has topic overview / conversation summary / avoid followup fields.
5. Child UI got a first thin-slice polish: Xiaobaihu panel background and phase chip.
```

Master review accepted Task 06 with closeout items:

```text
1. Parent settings UI hides time periods, but ViewModel still validates and resaves hidden schedule defaults. This should be cleaned up so hidden schedule controls do not affect saves or block family use.
2. Topic seeds are currently plain strings. Product design asked for reviewed/expiring/safety-noted seed packs. Upgrade the provider and tests without adding live web search.
3. Topic shift is mostly backend prompt/runtime. The child UI still lacks a small, safe “换个轻松话题”/topic seed surface when idle or topic_shift is recommended.
4. TTS perceived latency is still a real-device concern. Add observable timing and docs so the next QA can tell whether delay is model, TTS generation, network, or Android playback.
5. Father report is structurally improved, but it needs stricter tests/examples for a real CS/game conversation summary and model timeout/fallback naturalness.
```

Do not use this task to add broad new features. This is closeout/hardening.

---

## 1. Shared required reading

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_TASK_06_POST_DEVICE_QA_PRODUCT_REFINEMENT_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
backend/README.md
android/README.md
```

---

## 2. Coordination model

Suggested branches:

```text
codex/task07-a-parent-settings-schedule-closeout
codex/task07-b-topic-seed-pack-and-shift-ui
codex/task07-c-tts-latency-observability
codex/task07-d-parent-report-summary-hardening
```

Suggested merge order:

```text
1. Lane A first: parent profile/save behavior.
2. Lane B second: topic seed schema + optional UI chips.
3. Lane C third: timing observability, should not conflict heavily.
4. Lane D last: parent report docs/tests can reflect final data model.
```

---

# Lane A — Parent Settings Schedule Closeout

## A1. Goal

Fully align parent settings with freedom-first: hidden schedule/time-period controls must not block save, must not churn default schedule values, and must not imply hard conversation modes.

## A2. Requirements

```text
1. ParentSettingsScreen should keep child profile fields: nickname, display name, age, grade, call/gender preference, interests, topic boundaries, parent message, goals, communication preferences.
2. Visible schedule fields remain removed from v0.1 UI.
3. ParentPolicyViewModel should not validate hidden schedule fields on save.
4. Saving a policy should preserve existing schedule if present, but should not rewrite default after_school/homework/bedtime times just because hidden UI defaults exist.
5. Add tests covering: save with blank age, valid age, invalid age, and no schedule mutation when schedule is hidden.
6. Product docs should state: schedule remains backend-compatible/deprecated, not family beta visible, and not a hard mode driver.
```

## A3. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/parent/ParentPolicyViewModel.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentSettingsScreen.kt
android/app/src/test/java/com/childai/companion/ui/parent/*
android/app/src/test/java/com/childai/companion/data/parent/*
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
```

## A4. Do not do

```text
1. Do not remove backend schema compatibility for existing schedule data.
2. Do not add production accounts/auth.
3. Do not make gender/call preference drive interests, colors, hobbies, or ability assumptions.
```

## A5. Acceptance criteria

```text
1. Hidden schedule fields cannot block saving.
2. Hidden schedule defaults are not re-saved as a side effect.
3. Existing schedule is preserved when backend returns it.
4. Tests verify age validation and schedule preservation.
```

---

# Lane B — Topic Seed Pack Hardening and Child-facing Shift Chips

## B1. Goal

Upgrade topic seeds from plain strings to reviewed, age-aware, non-addictive seed objects, and add a tiny UI surface for safe topic shifts without live web/trending fetch.

## B2. Backend seed schema

Upgrade static seed pack to objects such as:

```json
{
  "id": "creative_building_blocks",
  "label": "积木/搭建",
  "age_bands": ["age_5_6", "age_7_8"],
  "prompt_hint": "可以问孩子最近有没有搭过什么东西，或愿不愿意拍给小白狐看。",
  "safety_notes": "avoid purchase pressure; avoid ranking/collection mechanics",
  "expires_at": "2026-12-31",
  "source": "curated_v0_1"
}
```

`TopicSeedService` should return safe labels for prompts/UI and keep metadata available for validation.

## B3. Child UI thin slice

If low-risk, add a small idle/low-engagement topic shift chip row in child chat:

```text
- “换个轻松话题”
- 1–2 seed labels from safe curated provider or local fallback
- “拍给小白狐看” remains available
```

This UI must not appear as a task menu, reward, streak, or retention hook. It should be visible only when idle/Ready, after topic_shift_recommended, or as quick actions returned by backend if already available.

If backend API does not yet expose seed labels to Android, implement only backend rich seed schema and document UI as next thin slice. Do not hack a second network call.

## B4. Allowed files

```text
backend/app/services/topic_seed_service.py
backend/app/data/topic_seed_packs_v0_1.json
backend/app/services/turn_guidance_builder.py
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/app/tests/**/*topic* or turn guidance tests
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## B5. Do not do

```text
1. Do not call web/search/live trend APIs in child chat.
2. Do not include unsafe memes, celebrity gossip, purchase pressure, ranking, collection mechanics, or “明天有惊喜”.
3. Do not encourage more game playing; game can be a topic, not an activity push.
```

## B6. Acceptance criteria

```text
1. Seed pack has id/label/age_bands/prompt_hint/safety_notes/expires_at/source.
2. Tests reject missing/expired/unsafe seed fields or at least validate loaded pack shape.
3. TurnGuidanceBuilder still recommends topic shift for CS-like low engagement.
4. If UI chips are implemented, they are small, optional, child-safe, and do not hide voice/TTS controls.
```

---

# Lane C — TTS Latency Observability and QA Hooks

## C1. Goal

Do not guess why voice playback feels delayed. Add enough timing fields/logs/docs to separate model delay, TTS generation delay, stream/audio-ready delay, and Android playback start delay.

## C2. Requirements

Backend:

```text
1. Ensure conversation stream logs include request_start, first_text_ms, tts_started_ms, first_audio_ms, turn_total_ms where available.
2. If `/conversation/message` non-stream path includes `audio_url`, log model_ms and tts_ms separately if possible.
3. Do not add raw child text or full model reply to timing logs.
```

Android:

```text
1. Add lightweight debug/logcat timing when remote audio URL is received and when playback actually starts/done/errors.
2. Include request_id or turn id when available.
3. Do not show debug timing to child UI by default.
```

Docs/QA:

```text
1. Add QA rows for “TTS perceived latency breakdown”.
2. Explain how to collect request_id + logcat/backend logs for one slow turn.
```

## C3. Allowed files

```text
backend/app/services/conversation_service.py
backend/app/services/conversation_stream_service.py
backend/app/services/tts_service.py
backend/app/core/logging.py
backend/app/tests/**/*tts* or stream tests
android/app/src/main/java/com/childai/companion/voice/*
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/voice/*
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## C4. Do not do

```text
1. Do not change TTS provider or voice clone strategy in this lane.
2. Do not reintroduce Android system TTS fallback.
3. Do not display latency/debug text to child.
```

## C5. Acceptance criteria

```text
1. One slow turn can be diagnosed into model vs TTS vs playback categories using logs.
2. Tests verify timing fields do not contain raw child text or full reply.
3. QA checklist explains exactly what to collect.
```

---

# Lane D — Parent Report Summary Hardening

## D1. Goal

Make the new father report topic/content summary robust enough for real family testing, especially for the CS/game scenario from the device video.

## D2. Requirements

```text
1. Add/strengthen synthetic test using CS/game conversation: friends/teams/map/loss/short replies.
2. Expected report should include a parent-readable topic overview, conversation summary, tonight bridge, and avoid_followup.
3. Ensure report does not show raw full transcript, provider/debug wording, or behavioral scoring.
4. Improve empty/model_failed state language if needed.
5. Add docs explaining v0.1 report is a summary, not raw transcript export. Future raw export/compliance is a separate design.
```

## D3. Allowed files

```text
backend/app/domain/parent_report.py
backend/app/services/parent_report_service.py
backend/app/tests/**/*parent_report*
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
android/app/src/test/java/com/childai/companion/ui/parent/*
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## D4. Do not do

```text
1. Do not add raw transcript display/export.
2. Do not claim legal/compliance readiness for future上市 raw record requests.
3. Do not turn parent report into a score/ranking/behavior dashboard.
```

## D5. Acceptance criteria

```text
1. CS/game synthetic report reads naturally to a parent.
2. It includes what was discussed at a summary level.
3. It includes what not to ask/avoid tonight.
4. UI renders topic cards without raw transcript.
```

---

## 3. Final response required from Codex

Codex must report:

```text
1. commit sha(s),
2. lanes completed,
3. files changed by lane,
4. test commands and exact results,
5. parent settings before/after behavior,
6. topic seed pack shape and example topic-shift output,
7. TTS latency log fields and how to collect one slow-turn trace,
8. father report synthetic CS/game before/after summary,
9. remaining Redmi K60 / Honor Pad 5 device QA items,
10. any product decisions changed.
```
