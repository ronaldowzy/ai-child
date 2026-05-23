# Prompt Child Speech Guidance v0.1

Status: implemented thin slice on 2026-05-22.

## Scope

This pass improves backend child_chat prompt engineering for voice-first child conversation. It does not change Android runtime, Android assets, DB schema, model providers, true LLM streaming, or CameraX.

## Static Prompt Changes

`global_system_v0_1.txt` now includes child speech understanding rules:

- Child speech may contain exaggeration, jokes, half-sentences, pauses, repetitions, bystander prompts, button-operation hints, or ASR mistakes.
- Do not treat every number, degree word, or danger-like word as an adult-accurate fact.
- For phrases like "每天十五公里", "累死了", "要死了", or "超级无敌", first reflect the likely feeling softly, then ask one small confirming question.
- If a turn contains both operation aside and child content, answer the child content first.
- If a turn sounds like a bystander, lightly confirm whether it is what the child wants to say and do not write it to long-term memory.

`conversation_open_v0_1.txt` now includes topic progression and track-switching rules:

- After roughly three rounds on one ordinary topic, offer a light switch unless the child is clearly engaged.
- If the child asks to change topic, stop pursuing the old topic.
- Offer two concrete, easy directions instead of abstract open-ended questions.
- Preserve interests such as running, competitions, animals, drawing, blocks, or stories as light seeds without forcing the topic.

## Runtime Turn Guidance

`PromptLayer.TURN_GUIDANCE` is now inserted after scene prompt and before memory context. `ChildAgentRuntime` builds this section from current child text and recent user history.

Current hints:

- `possible_operation_aside`: operation or button prompt may be present; answer the real child content.
- `possible_child_exaggeration`: numbers or degree words may be exaggerated, playful, or ASR-unstable.
- `body_discomfort_watch_lite`: sports/play context plus "要死了/累死了/快不行了/喘死了"; do one soft check and then avoid prolonged medical questioning if pain is denied.
- `child_requests_topic_change`: respect the topic change and stop pursuing the old topic.
- `bedtime_close_requested`: short closeout, no new question.
- `same_topic_too_long`: recent repeated ordinary topic plus short/boundary reply; offer a switch.

This section is internal prompt context and must not be exposed to the child.

## Safety And Intent

SafetyEngine keeps explicit self-harm language critical:

- "不想活", "想死", "自杀", "伤害自己" remain `SELF_HARM` / `CRITICAL`.

Sports-context exaggerated fatigue is now watch-lite:

- "跑完要死了", "跑步累死了", "比赛后快不行了" become LOW medical/body-discomfort hints, not self-harm.
- Serious symptoms such as chest pain, difficulty breathing, dizziness, vomiting, unstable standing, bleeding, or medication mistakes still enter medical WATCH.

IntentClassifier maps watch-lite child speech to `EMOTION_EXPRESSION` with sub-intent `body_discomfort_watch_lite` or `exaggerated_fatigue`, instead of escalating to high-risk intent.

## Runtime Output Hardening

PROMPT-REAL-HARDEN-1 adds deterministic child-facing safeguards after real MiMo trace review:

- Critical self-harm turns use a fixed 5-10-year-old-friendly trusted-adult reply instead of relying on model wording.
- Parenthetical stage directions such as "（用温和的语调）" are stripped before the child sees or hears the reply.
- Ordinary child_chat replies keep at most one main question.
- Bedtime closeout removes open questions and "tomorrow hook" wording such as continuing the topic tomorrow.
- Explicit topic-change requests are not echoed verbatim back to the child.

The latest synthetic real-provider trace has P0/P2 none for child-facing output. Remaining P1 items are provider raw empty responses for opening/parent_report, with runtime fallback covering the child-facing text.

## Parent Report Extraction

ParentReportService now treats sports/competition/running phrases as a sports topic, not learning help. It also recognizes topic-change requests as boundary/transition expression and describes "要死了/累死了" in sports context as post-run exaggerated fatigue, not self-harm.

Learning help is only detected from explicit homework/problem/help markers such as homework, math problem, language homework, "这道题怎么做", or "我有一道题不会". Generic "话题" or "比赛" no longer triggers learning help.

## QA Notes

Regression tests cover the real voice sequence:

1. Button aside plus competition announcement.
2. Sports competition/running follow-up.
3. "每天十五公里" exaggeration.
4. "跑完感觉是要死了" watch-lite handling.
5. Topic change.
6. Bedtime closeout.

Redmi K60 and Honor Pad 5 manual QA still needs to validate whether the generated live replies feel natural with real MiMo responses.

True LLM token streaming and CameraX remain unimplemented and were not touched in this pass.
