# Codex Task 06: Post-device QA Product Refinement v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: product refinement after first real-device test video  
Source: first Redmi K60 real-device test video and product owner feedback on 2026-05-24  
Recommended mode: four Codex lanes on separate branches/worktrees; if only one Codex session is available, execute Lane A -> Lane B -> Lane C -> Lane D.

---

## 0. Why this task

A real-device test video shows that the core loop now runs: parent entry/settings, voice-first conversation, TTS stop/mute, camera/image share, and father report can be exercised. However, the experience still feels like an intermediate build rather than a child-facing companion product.

Observed and owner-reported issues:

```text
1. Parent settings still expose time-period/schedule fields whose product value is decreasing under freedom-first; they may also bias the dialog away from free conversation.
2. Parent settings lack basic child profile fields such as age and gender/call-preference.
3. Voice input ASR speed/accuracy feels good, but TTS/audio reply latency still feels high.
4. The conversation stays on the same topic too long. In the video, after 2-3 CS/game turns, Xiaobaihu keeps digging into team/play details instead of sensing that the child may want a topic shift.
5. Trending topic discovery may help Xiaobaihu propose better alternatives, but it must be child-safe, curated, and non-addictive.
6. Father report is still too mechanical; parents need at least a clear topic/content summary, not raw transcripts, while respecting privacy and not creating surveillance pressure.
7. The current UI is functional but visually plain; it needs a child-friendly but orderly home/chat polish layer.
```

This task should not start from scratch. It must preserve all Task 01-05 improvements.

---

## 1. Shared required reading

Read before coding:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
backend/README.md
android/README.md
```

Also inspect the relevant code before changing:

```text
backend/app/domain/schemas/parent_policy.py
backend/app/services/parent_policy_service.py
backend/app/services/prompt_manager.py
backend/app/services/opening_policy.py
backend/app/services/parent_report_service.py
backend/app/services/turn_guidance_builder.py
backend/app/services/child_agent_runtime.py
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/main/java/com/childai/companion/ui/chat/*
android/app/src/main/java/com/childai/companion/data/*
```

If exact paths differ, search current repo and adapt.

---

## 2. Coordination model

Use separate branches if multiple Codex agents are available:

```text
codex/e10-parent-profile-settings-v0-1
codex/e11-topic-shift-and-trend-seeds-v0-1
codex/e12-parent-report-summary-v0-1
codex/e13-child-ui-polish-spec-v0-1
```

Suggested merge order:

```text
1. Lane A first: parent profile schema/UI can feed prompt and reports.
2. Lane B second: topic-shift logic can use age/profile.
3. Lane C third: parent report can use updated profile and topic summary.
4. Lane D last: UI polish should reflect final product state and not fight other UI changes.
```

If only one Codex session is available, execute A -> B -> C -> D sequentially.

Do not run broad refactors across lanes. If docs conflict, resolve `CODEX_PROGRESS_BOARD` after all lanes.

---

# Lane A — Parent Settings: Child Profile Simplification

## A1. Goal

Simplify parent settings around freedom-first. Replace or demote low-value hard schedule/time-period controls, and add explicit child profile basics.

The app should know enough about the child to adapt language safely, but should not invite stereotype-based personalization.

## A2. Product decisions for this lane

Implement these as code + docs:

```text
1. Visible schedule/time-period settings are deprecated for v0.1 family beta unless they are only used for gentle sleep/availability hints. Do not let schedule hard-lock conversation scenes.
2. Add child age or age band as a required/strongly encouraged parent setting.
3. Add grade as optional.
4. Add gender/call-preference as optional. Use it only for respectful wording/profile context, never for stereotypes or content assumptions.
5. Keep child nickname and display name.
6. Keep parent message/goals, but avoid forcing them into child-visible wording.
7. Add optional child interests and topic boundaries if easy; otherwise document for next task.
```

Recommended visible fields:

```text
- 小名 / 孩子希望小白狐怎么叫 TA
- 显示名（可选）
- 年龄 or 出生年份 / 年龄段
- 年级（可选）
- 性别/称呼偏好（可选：男孩/女孩/不填写/自定义称呼偏好；avoid stereotypes）
- 孩子最近喜欢的话题（可选，comma-separated in v0.1）
- 不想聊/要避开的主题（可选）
- 父母寄语
- 本周目标
```

Remove or demote from visible v0.1 UI:

```text
- after_school_start/end hard schedule
- homework_start/end hard schedule
- bedtime_start/end hard schedule
```

If backend schema still needs backward compatibility, keep schedule fields as optional/deprecated and do not show them prominently in Android.

## A3. Allowed files

```text
backend/app/domain/schemas/parent_policy.py
backend/app/services/parent_policy_service.py
backend/app/services/prompt_manager.py
backend/app/services/opening_policy.py
backend/app/repositories/*parent_policy*
backend/app/db/models.py
backend/app/db/migrations/* or alembic versions if schema change is needed
backend/app/tests/**/*parent_policy* or related tests
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/main/java/com/childai/companion/data/parent/*
android/app/src/test/java/com/childai/companion/ui/parent/*
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
```

Prefer no DB migration if existing JSON policy can store these fields. If DB schema is fixed columns only, make the smallest compatible migration.

## A4. Do not do

```text
1. Do not use gender to assume interests, behavior, colors, games, language ability, or personality.
2. Do not remove backend schedule compatibility if existing stored policies may contain schedule.
3. Do not make the child enter these settings; this is parent-side only.
4. Do not add production auth/account system in this lane.
```

## A5. Acceptance criteria

```text
1. Parent settings UI shows age/age-band and optional gender/call-preference.
2. Visible schedule/time-period controls are removed, demoted, or clearly marked as not driving hard modes.
3. PromptManager receives age/profile context and does not expose internal labels to child.
4. Existing policies without age/gender still work with safe defaults.
5. Tests cover saving/loading child profile fields and prompt injection.
```

---

# Lane B — Conversation Topic Shift and Curated Trend Seeds

## B1. Goal

Reduce over-deepening of a single topic and give Xiaobaihu safe ways to offer fresh topics when the child appears done.

This lane should fix the test-video issue: after the child gives short/low-energy replies or the same topic has already gone 2-3 turns, Xiaobaihu should not keep interviewing. It should offer a gentle topic switch or let the child choose.

## B2. Product principles

```text
1. Children often lose interest quickly; do not treat every short answer as permission to dig deeper.
2. Topic continuation should be child-led. Xiaobaihu may continue if the child adds new details, asks a question, shows excitement, or directly says they want to continue.
3. If engagement appears low, Xiaobaihu should offer two or three easy alternatives: continue current topic / switch topic / show or tell something.
4. Do not use trending topics to lure the child into longer usage. Trend seeds are conversation rescue tools, not retention hooks.
5. Runtime web browsing should not be used in child chat v0.1. Use curated, reviewed, expiring topic seed packs.
```

## B3. Implement a v0.1 topic shift policy

Add or extend turn guidance with fields similar to:

```text
same_topic_turn_count
child_engagement_signal: high / medium / low / unknown
topic_shift_recommended: true/false
topic_shift_reason: repeated_short_answers / same_topic_too_long / boundary_signal / correction / low_energy
suggested_topic_seeds: list[str]
```

Heuristics:

```text
- If same topic >= 3 assistant turns and child reply is short/flat, topic_shift_recommended=true.
- If assistant asked 2 consecutive questions, next turn should not ask another deepening question.
- If child reply gives only factual closure, e.g. “最后我们输了”, respond with empathy + optional switch.
- If child adds vivid detail or asks a question, continue current topic but keep it short.
```

Example desired response after the CS sequence:

```text
输了会有点不甘心。这个话题我们可以先放一放。你想换成聊游戏里的搞笑瞬间、今天看到的东西，还是拍给我看一个东西？
```

## B4. Curated trend seed provider v0.1

Implement a small static/JSON provider, not live web scraping:

```text
backend/app/services/topic_seed_service.py
backend/app/data/topic_seed_packs/age_5_6.json
backend/app/data/topic_seed_packs/age_7_8.json
backend/app/data/topic_seed_packs/age_9_10.json
```

Seed format:

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

Initial seed categories should be generic and safe:

```text
- building/blocks/lego-like play
- drawing/handcraft
- dinosaurs/animals
- sports/running/ball games
- funny moments
- simple stories
- toys/collections without purchase pressure
- school project/show-and-tell
- nature/weather/plant observation
- safe games as topic only, not gameplay encouragement
```

Do not include raw hot memes that may be unsafe or short-lived without review.

## B5. Allowed files

```text
backend/app/services/turn_guidance_builder.py
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/app/services/topic_seed_service.py
backend/app/data/topic_seed_packs/*.json
backend/app/tests/**/*turn_guidance* or topic seed tests
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## B6. Do not do

```text
1. Do not call live web/search APIs in child chat.
2. Do not recommend games in a way that encourages playing more.
3. Do not add addictive hooks, rewards, streaks, FOMO, or “明天有惊喜”.
4. Do not hard-code celebrity/news/short-video memes as child prompts without review.
```

## B7. Acceptance criteria

```text
1. A CS/game-like 3-turn conversation with short child replies triggers topic_shift_recommended.
2. The next reply offers switch/choice rather than deepening current topic.
3. Age-band specific safe topic seeds are available and tested.
4. Prompt guidance makes trend seeds optional and non-addictive.
5. Tests cover low engagement vs high engagement distinction.
```

---

# Lane C — Father Report: Topic and Content Summary Redesign

## C1. Goal

Make father daily report understandable and useful. It should report what topics the child talked about and summarize content at a high level, without exposing raw transcripts or creating surveillance pressure.

## C2. Product principle

Parents/guardians have a legitimate need to understand broad conversation content and safety/learning signals. The app should provide a clear summary, not raw logs by default.

Report structure v0.1 should become:

```text
1. 今日聊天主题概览
2. 主题内容摘要
3. 孩子的表达/情绪/学习观察
4. 可继续现实接话的一句话
5. 建议避免的追问方式
6. 安全/隐私/学习注意事项
7. 数据边界说明：不是逐字记录；如需原始记录需另行设计家长导出/合规流程
```

Suggested schema fields:

```text
topic_overview: list[{topic, child_intent, summary, emotion_tone, parent_bridge}]
conversation_summary: string
expression_observations: list[str]
learning_observations: list[str]
emotion_observations: list[str]
safety_alerts: list[str]
tonight_parent_bridge: string
avoid_followup: string
```

Existing fields should remain backward-compatible.

## C3. Model prompt requirements

Parent report prompt must explicitly say:

```text
- Summarize topics and content in plain parent-readable language.
- Do not quote full child turns or full assistant turns.
- Do not expose provider/debug/prompt wording.
- Do not sound like surveillance.
- Include concrete enough content for a parent to understand what was discussed.
- If there was little material, say so plainly.
```

## C4. Android UI requirements

Parent report UI should show:

```text
Top: 今晚可以怎么接一句
Then: 今日聊了什么
Then: 每个主题 card, e.g. “游戏/CS：孩子说和几个朋友一起玩，两组对战，最后输了；小白狐鼓励他下次再试。”
Then: 表达/情绪/学习观察
Then: 需要留意
```

Avoid vague mechanical headings. Prefer parent-readable copy.

## C5. Allowed files

```text
backend/app/domain/parent_report.py
backend/app/services/parent_report_service.py
backend/app/prompts/**/*parent_report*
backend/app/repositories/*parent_report*
backend/app/tests/**/*parent_report*
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportViewModel.kt
android/app/src/main/java/com/childai/companion/data/parent/*
android/app/src/test/java/com/childai/companion/ui/parent/*
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## C6. Do not do

```text
1. Do not display raw full chat transcript in v0.1.
2. Do not add parent export/download of raw transcript in this task.
3. Do not claim compliance for future上市/legal exports; mark as future design.
4. Do not make father report a behavioral scoring dashboard.
```

## C7. Acceptance criteria

```text
1. Parent report includes a readable topic/content summary.
2. Test scenario based on CS/game conversation produces parent-readable topic overview.
3. Failure/empty state remains family-readable.
4. No raw transcript or provider/debug wording is shown.
5. Android UI renders topic overview cards.
```

---

# Lane D — Child UI Polish Specification and Thin Slice

## D1. Goal

Improve the child-facing UI from an engineering intermediate screen toward a polished companion surface, without adding addictive mechanics.

This lane may implement a small safe visual thin slice, but must start with a documented design spec.

## D2. Product direction

The interface should be:

```text
- warm but clean,
- child-friendly but not noisy,
- centered on Xiaobaihu,
- voice-first,
- simple enough for 5–10,
- free of streaks, points, gacha, missions, and pressure.
```

Ideas to specify and, if feasible, thin-slice implement:

```text
1. Xiaobaihu left panel: richer background card, soft gradient, small “mood/status chip”.
2. Conversation area: fewer hard rectangular bubbles; better spacing and readable font size.
3. Topic switch chips: “换个轻松话题”, “讲个小故事”, “拍给小白狐看”, “我想休息”.
4. A small “今天可以聊” area with 2-3 safe curated topic seeds, only when idle or low engagement.
5. Parent entry remains small and unobtrusive.
6. No gamification or collection wall in v0.1.
```

## D3. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/ui/theme/*
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## D4. Do not do

```text
1. Do not add points, badges, streaks, daily rewards, pet hunger, or FOMO.
2. Do not hide critical controls like stop/mute/retry.
3. Do not make the UI visually too busy for low-end Honor Pad 5.
4. Do not add new asset packs unless tiny and justified.
```

## D5. Acceptance criteria

```text
1. `docs/CHILD_UI_POLISH_DESIGN_V0_1.md` exists and states what is implemented vs future.
2. At least one safe polish thin slice lands if low-risk: e.g. Xiaobaihu panel/background/status chip/topic seed chips.
3. Voice-first controls remain prominent.
4. Parent entry remains low-emphasis.
5. Compose/JVM tests or screenshot-preview-friendly tests are updated where possible.
```

---

## 3. Cross-lane documentation updates

Final merge should update:

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Rules:

```text
1. Mark code-complete separately from device QA.
2. Real-device video observations should be summarized without raw child/private data.
3. Do not claim production compliance for raw transcript exports.
4. Do not claim trend service is live unless implemented as reviewed static seed packs only.
```

---

## 4. Final Codex response requirements

Codex must report:

```text
1. commit sha(s),
2. lanes completed,
3. exact files changed by lane,
4. test commands and exact results,
5. what changed in parent settings,
6. topic-shift examples before/after,
7. father report before/after example using synthetic data,
8. UI polish screenshots or preview notes if available,
9. remaining device QA items,
10. whether any real-device QA was actually performed.
```
