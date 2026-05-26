# DOCUMENT_GOVERNANCE_AND_UNIMPLEMENTED_ROADMAP_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Purpose: current source of truth for document cleanup, implementation reality, and planned-but-not-yet-implemented product work.  
Created after family-beta testing feedback that parent report still felt stiff and bug-prone.

---

## 0. Why this document exists

The repository accumulated many process docs while rapidly iterating through Tasks 21-26. Some were useful for implementation review but are now misleading as future planning sources.

This document consolidates:

```text
1. which documents were removed as obsolete process docs;
2. which design docs remain valid but need updated interpretation;
3. current implementation reality;
4. all major planned-but-not-yet-implemented product directions;
5. for each direction: current state -> target state -> implementation details.
```

Future master sessions should use this document before choosing the next task.

---

## 1. Deleted obsolete process documents

The following documents were removed because they described completed, corrected, paused, or superseded single-round implementation work:

```text
docs/CODE_AGENT_TASK_21_OPENING_AND_PARENT_REPORT_VISIBLE_QUALITY_V2.md
docs/CODE_AGENT_TASK_22_XIAOBAIHU_RUNTIME_VISUAL_TRANSITION_THROTTLE_V0_1.md
docs/CODE_AGENT_TASK_22_CORRECTION_COMPOSE_RUNTIME_HOLD_TIMER_V0_1.md
docs/CODE_AGENT_TASK_23_SHOW_AND_TELL_VISIBLE_QUALITY_V3.md
docs/CODE_AGENT_TASK_25_VOICE_FIRST_CONVERSATION_POLISH_V0_1.md
docs/CODE_AGENT_TASK_25_LANGUAGE_LOGIC_REWRITE_ROUND2_V0_1.md
```

Rationale:

```text
1. Task 21 opening / parent report visible-quality work has already been implemented and then superseded by later parent report redesign.
2. Task 22 runtime anti-flicker and its correction have already been implemented and reviewed.
3. Task 23 show-and-tell visible quality has already been implemented and reviewed.
4. Old Task 25 voice-first polish was paused before implementation.
5. Task 25 language rewrite was superseded by Task 26 parent report narrative v3 redesign after real testing showed the stitched-report approach was not good enough.
```

The current active process task is:

```text
docs/CODE_AGENT_TASK_26_PARENT_REPORT_NARRATIVE_V3_REDESIGN.md
```

Do not restore old task docs unless investigating history.

---

## 2. Current implementation reality

### 2.1 Implemented / mostly implemented

```text
1. Android voice-first child chat: tap-to-record, backend ASR, default auto-send transcript.
2. Backend local SenseVoice ASR priority path with MiMo fallback guardrails.
3. Backend MiMo VoiceClone audio_url path and Android remote audio playback.
4. Android child-facing phase reducer / presentation model for listening, recognizing, thinking, speaking, image processing, retry, permission, and service-error states.
5. Xiaobaihu visual state resolver and runtime min-hold anti-flicker logic.
6. Freedom-first interaction: default conversation.open, with safety/privacy/learning/bedtime as guardrails.
7. Universal image sharing: system camera/gallery upload, backend image context, show-and-tell visible-quality fallback.
8. Opening greeting v3: personalized but short, with corrected bedtime low-stimulation behavior.
9. Parent-operated account thin slice for family beta.
10. Parent settings / child profile / parent message / nickname context.
11. Healthy Engagement core prohibitions: no points, streaks, ranking, gacha, pet hunger, FOMO, secret-friend hooks, or raw transcript export.
12. Parent report service exists and is being redesigned in Task 26 from stitched fields to coherent narrative.
```

### 2.2 Implemented but not fully validated by device QA

```text
1. Redmi K60 / Honor Pad 5 real-device layout and performance.
2. Voice input accuracy and latency with actual child speech/noise.
3. MiMo VoiceClone first-audio latency and family-network behavior.
4. Image upload, local preview, orientation, timeout, and vision follow-up on real devices.
5. TTS stop/mute controls and segment ordering under real usage.
6. Parent report v3 once Task 26 lands.
```

### 2.3 Known current product problem

```text
Parent report v2 / previous language rewrite approach still felt like stiff assembled fragments in real testing. This invalidated the small-patch strategy. Task 26 now changes the architecture of the report output: model-written coherent narrative first, minimal deterministic fallback second.
```

---

## 3. Design docs that remain valid, with updated interpretation

### 3.1 `PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md`

Still valid as a long-term roadmap, but the “after Task 09 / next expected sequence” parts are historical. Current reality is now after Tasks 21-26 and real testing feedback.

Updated interpretation:

```text
1. Parent report trust/readability is the current highest-priority repair.
2. Device QA remains important, but should not stop scoped product progress.
3. Relationship memory v2, voice/latency maturity, image sharing v2, and governance remain future work.
```

### 3.2 `EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md`

Still valid as the experience optimization backbone, but many P0/P1 items have been partially implemented.

Updated interpretation:

```text
1. ChildTurnUiPhase / interaction state thin slice has been implemented.
2. TTS stop/mute visibility has been partially implemented.
3. Image sharing concrete feedback has been partially implemented.
4. Parent report remains the biggest trust/readability gap and is being redesigned.
5. Voice-first polish and first-audio latency remain pending.
```

### 3.3 `FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md`

Still valid and aligned with current direction.

Important current rules:

```text
1. Default is conversation.open.
2. Time, image, memory, and parent message are context, not hard modes.
3. Bedtime should not immediately block chatting; it should lower stimulation and support natural closure.
4. Explicit learning/homework, safety, and privacy remain hard guardrails.
```

### 3.4 `UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md`

Still valid, but early lines about “mock first” are historical. Current implementation uses real camera/gallery upload and backend vision/image context, while CameraX remains deferred.

Updated interpretation:

```text
1. “拍给小白狐看” is the product-level image action.
2. Homework is only one branch, not the default interpretation.
3. Parent report should summarize image sharing as broad expression, not ask what exact image was shown to Xiaobaihu.
4. CameraX and long-term gallery are deferred.
```

### 3.5 `VOICE_INTERACTION_DESIGN_V0_1.md`

Still valid, though it contains historical design evolution. Current source of truth:

```text
1. Child default is tap-to-record voice-first.
2. No always-on mic, no wake word, no streaming ASR in v1.
3. ASR priority is backend local SenseVoice, with MiMo fallback only through policy gates.
4. Child-facing TTS uses backend audio_url; Android system TTS is not a formal Xiaobaihu voice fallback.
5. Voice-first polish remains pending after parent report v3 stabilizes.
```

### 3.6 `HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md`

Still valid as north-star design. Many systems described there remain unimplemented or partial.

Updated interpretation:

```text
1. Prohibited engagement mechanics are already policy-level hard rules.
2. Healthy engagement metrics and child-control observability are still not complete product systems.
3. Growing Nest / expression footprint /共同项目 UI are future work and should not be built until core chat/report quality stabilizes.
```

---

## 4. Planned but not yet implemented: large directions

## Direction A — Parent Report Narrative v3

### Current state

```text
Parent report exists, but recent real testing showed it still feels stiff and assembled from fragments. Small wording corrections are not enough.
```

### Target state

```text
A parent receives one short, coherent, natural Chinese daily note. It reads like a human-written family connection note, not a monitoring log, teacher evaluation, or usage-statistics report.
```

### Implementation details

```text
1. Use a whole-report-first model prompt.
2. Feed curated safe summaries, not raw transcript-like snippets.
3. Keep schema compatibility if needed, but make summary/conversation_summary/tonight_parent_bridge internally coherent.
4. Make deterministic fallback intentionally minimal and honest.
5. Remove exact message counts.
6. For image sharing, use open family invitation language, not “what did you show Xiaobaihu?”
7. Add visible-quality tests for normal, image, learning, and safety days.
```

### Current -> target comparison

```text
Before: stitched fields, many independent snippets, sometimes awkward or monitoring-like.
After: one coherent daily note, one realistic parent bridge, minimal avoid list.
```

### Status

```text
Active: Task 26.
```

---

## Direction B — Voice-first conversation polish

### Current state

```text
Voice-first tap-to-record, backend ASR, auto-send, TTS playback, stop/mute controls, and child-facing phases exist. However real child/family voice use still needs clarity, responsiveness, and error polish.
```

### Target state

```text
The child always understands whether Xiaobaihu is listening, understanding, thinking, speaking, or needs retry. Stop, mute, retry, cancel, and start speaking again feel natural and non-technical.
```

### Implementation details

```text
1. Ensure starting recording always stops current TTS and clears queued audio safely.
2. Make retry/cancel/permission/network copy non-technical.
3. Keep confirm-before-send only in DevSettings / parent debug.
4. Confirm mute prevents future auto-read but does not hide text.
5. Ensure late opening never interrupts active child voice flow.
6. Add Android ViewModel and UI tests around state transitions.
```

### Current -> target comparison

```text
Before: functionally works, but still feels like operating a voice button and waiting through states.
After: feels like taking turns with Xiaobaihu: talk, wait, hear, stop, retry.
```

### Status

```text
Planned. Old Task 25 was removed because it was premature; should be recreated after Task 26 passes.
```

---

## Direction C — First response / text-first audio-follow experience

### Current state

```text
Streaming and TTS audio segments exist, but real tests showed slow MiMo VoiceClone and opening/model latency can still make turns feel unresponsive. Some timeouts were adjusted, but latency is not yet productized.
```

### Target state

```text
Text appears quickly, Xiaobaihu visibly starts thinking/speaking, and audio follows naturally. If audio is slow or fails, the child still feels the conversation continued.
```

### Implementation details

```text
1. Keep measuring first_text_ms, tts_started_ms, first_audio_ms, Android playback start.
2. Optimize first sentence length and split points.
3. Consider greeting/common short phrase TTS cache after evidence.
4. Do not reintroduce system TTS as Xiaobaihu voice.
5. Do not hide latency with addictive animations.
```

### Current -> target comparison

```text
Before: text/audio can feel slow or inconsistent; user needs logs to diagnose.
After: perceived responsiveness is stable even when audio generation is slower.
```

### Status

```text
Planned after parent report v3 and voice-first polish.
```

---

## Direction D — Relationship Memory v2 / gentle continuity

### Current state

```text
Interest seed, unfinished thread, show-and-tell memory, proud moment, and topic boundary concepts exist in backend. Opening and reports use some memory. The behavior is still thin and can feel rule-like if overused.
```

### Target state

```text
Xiaobaihu lightly remembers what the child cares about, but does not track, pressure, label, or repeatedly pull the child back to old topics.
```

### Implementation details

```text
1. Add frequency limits and decay for memory callbacks.
2. Separate child-facing memory use from parent-report memory use.
3. Use “soft recall” wording with easy refusal.
4. Respect bedtime, low-expression, and boundary modes.
5. Never use memory for dependence hooks such as “I waited for you”.
6. Add tests for low-pressure recall and do-not-recall scenarios.
```

### Current -> target comparison

```text
Before: memory exists as structured hints and some opening/report usage.
After: memory becomes a gentle continuity layer with explicit non-pressure rules.
```

### Status

```text
Planned.
```

---

## Direction E — Conversation Arc v2

### Current state

```text
Freedom-first, turn guidance, question throttle, topic shift, bedtime, and conversation_control exist as partial mechanisms. There is not yet a single explicit ConversationArcState.
```

### Target state

```text
Each session has a gentle arc: welcome, child-led topic, brief deepening, stop/shift detection, optional parent bridge, and calm close. The child can always stop or change topic.
```

### Implementation details

```text
1. Define ConversationArcState in backend or runtime context.
2. Track whether current turn is opening, exploring, deepening, shifting, closing, or boundary-respecting.
3. Limit consecutive questions and long replies based on age band.
4. Surface child stop/shift intent to Android and memory/report systems.
5. Add synthetic trace tests for short replies, boundary requests, high engagement, and bedtime.
```

### Current -> target comparison

```text
Before: scattered rules manage pacing.
After: a clear arc model controls pacing and closure.
```

### Status

```text
Planned.
```

---

## Direction F — Healthy Engagement metrics and QA

### Current state

```text
The product forbids unhealthy mechanics, and some prompt/runtime rules exist. Metrics for healthy engagement are not complete.
```

### Target state

```text
The system can detect and test whether it is respecting stop/shift signals, not over-questioning, not extending bedtime, and not creating dependency.
```

### Implementation details

```text
1. Track consecutive agent questions.
2. Track child stop/shift signals and whether they were respected.
3. Track bedtime extension risk.
4. Track session duration bands, not as a retention target but as a safety signal.
5. Add QA scenarios for “I don’t want to talk”, “change topic”, “I’m sleepy”, and short replies.
6. Do not store raw transcript for this; use safe counters/signals.
```

### Current -> target comparison

```text
Before: healthy engagement is mostly policy and prompt-level.
After: healthy engagement has observable, testable signals.
```

### Status

```text
Planned.
```

---

## Direction G — Image sharing v2 / creative scaffolds

### Current state

```text
Real image upload, image context, and show-and-tell fallback exist. CameraX, long-term gallery, and creation loops are not implemented.
```

### Target state

```text
“拍给小白狐看” becomes a natural expression and creation loop: the child shares a drawing/toy/object/nature observation, Xiaobaihu notices one safe detail, and the child can tell a story or ask a question.
```

### Implementation details

```text
1. Improve follow-up chips only when they do not crowd voice-first controls.
2. Add creative prompts such as story/name/what-happened-next only after child intent is clear.
3. Keep homework as explicit branch only.
4. Keep parent report image summary broad and non-monitoring.
5. CameraX and long-term gallery remain deferred.
```

### Current -> target comparison

```text
Before: image sharing works and has visible-quality fallback.
After: image sharing supports richer child-led creation without becoming gallery/social/sharing product.
```

### Status

```text
Partially implemented; v2 planned later.
```

---

## Direction H — Learning scaffold v2

### Current state

```text
Learning/homework help scene exists and has been prompt-polished to avoid direct answer-giving. It remains a relatively simple scaffold.
```

### Target state

```text
Xiaobaihu helps the child understand the question, identify what they know, take one next step, and avoid outsourcing final answers.
```

### Implementation details

```text
1. Improve homework intent detection.
2. Distinguish “sharing a worksheet image” from “asking for help”.
3. Add step-level scaffold state: understand question -> known info -> hint -> child attempt -> next hint.
4. Add final-answer guardrails and tests.
5. Parent report learning note should be coherent narrative, not teacher evaluation.
```

### Current -> target comparison

```text
Before: prompt-level learning help.
After: structured scaffold with child agency and tests.
```

### Status

```text
Planned.
```

---

## Direction I — Parent governance and compliance foundation

### Current state

```text
Family-beta account/session thin slice exists. Production auth, multi-child/multi-guardian, consent, data deletion UI, retention policy UI, and compliance flows are not complete.
```

### Target state

```text
A parent-operated governance layer suitable for broader pilot, with clear consent, retention, deletion, account security, and child-data controls.
```

### Implementation details

```text
1. Harden auth and session management.
2. Add data retention/deletion controls.
3. Clarify audio/image/text retention policy in UI.
4. Add export policy only for summaries unless raw records become legally/product-wise required.
5. Add multi-child/multi-guardian only after family-beta validates single-child path.
```

### Current -> target comparison

```text
Before: family-beta thin slice.
After: production-oriented parent governance foundation.
```

### Status

```text
Later, not current priority.
```

---

## Direction J — Growing Nest / expression footprint UI

### Current state

```text
Design docs mention growth observation, common projects, and expression footprint. No full UI exists.
```

### Target state

```text
A low-stimulation, non-gamified way for parent/child to see broad expression growth or small creations over time, without points, streaks, badges, or pressure.
```

### Implementation details

```text
1. Use summaries and child-approved artifacts, not raw transcript.
2. Avoid daily streaks, achievement badges, and ranking.
3. Prefer gentle “recent little things” or “things we made/talked about” framing.
4. Build only after parent report, voice loop, and memory continuity are stable.
```

### Current -> target comparison

```text
Before: only design concept.
After: optional low-pressure reflection surface.
```

### Status

```text
Deferred.
```

---

## 5. Recommended next sequence after Task 26

```text
1. Review Task 26 parent report narrative v3 implementation.
2. Run focused parent report generation tests with normal/image/learning/safety examples.
3. If acceptable, run a small APK test focused only on parent report readability and no regression in child chat.
4. Then create a new voice-first conversation polish task from Direction B.
5. After that, evaluate first-response/audio latency from real evidence.
6. Then revisit relationship memory v2 and conversation arc v2.
```

Do not return to old stitched parent-report design.

---

## 6. Documentation rules going forward

```text
1. Single-round task docs should be deleted or archived once implemented and superseded.
2. Long-term design docs should remain, but this document should record how to interpret historical sections.
3. New product work should start from current implementation reality, not from old task documents.
4. If a real test invalidates a design approach, create a replacement task rather than continuing local patches.
5. Keep the repository biased toward fewer, current, high-signal docs.
```
