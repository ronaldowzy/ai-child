# MASTER_COLLABORATION_AND_FORWARD_MOTION_RULES_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Purpose: preserve the agreed multi-session collaboration model and prevent the project from stalling around short-term QA/package loops.

---

## 0. Why this document exists

The project now uses multiple ChatGPT / code-agent sessions in parallel. To keep momentum, every session must understand its own responsibility and avoid drifting into another role.

This document records three durable operating rules:

```text
1. Role ownership: master session designs and plans; code agents implement; Xiaobaihu visual design session owns character visual optimization.
2. QA cadence: APK/device testing is batch validation and may happen at night; it must not block daytime product/code progress.
3. Forward motion: known optimization backlog should keep pushing the project forward; do not get stuck circling around one or two small fixes.
```

---

## 1. Role ownership

### 1.1 Master ChatGPT session

The master session is the project planning and design owner.

Responsibilities:

```text
1. product direction and prioritization;
2. child psychology / education / healthy engagement boundaries;
3. conversation behavior design;
4. prompt design and prompt text changes;
5. opening greeting strategy;
6. parent report structure, wording, and model payload design;
7. task splitting for code agents;
8. GitHub main synchronization and code review;
9. deciding whether a submitted task passes, needs correction, or should be followed by a new task;
10. maintaining product docs and roadmap docs.
```

The master session may directly modify documentation and prompt-related project content when the change is primarily design/copy/policy, not implementation plumbing.

The master session should not wait for code agents to invent product wording. For design-sensitive areas, the master session provides the behavior and wording first.

Design-sensitive areas include:

```text
Xiaobaihu persona,
child conversation prompts,
opening strategy,
parent report prompt and wording,
child-facing UI copy,
parent-facing UI copy,
healthy engagement rules,
learning help behavior,
image/show-and-tell response style,
mascot visual state usage.
```

### 1.2 Code implementation agents

Code agents implement the exact task documents and should avoid independent product design.

Responsibilities:

```text
1. read the required docs before coding;
2. follow the task document scope exactly;
3. make small, reviewable code changes;
4. add/adjust tests;
5. report commit sha, files changed, exact test commands/results, and deviations;
6. ask the master session when product behavior, prompt wording, UI copy, or child-safety interpretation is unclear.
```

Code agents should not:

```text
1. rewrite prompts or parent-report wording on their own;
2. create new child-facing product copy without master approval;
3. expand scope into auth/TTS/ASR/image upload/navigation/assets unless explicitly allowed;
4. turn QA blockers into unrelated refactors;
5. introduce gamification, retention hooks, secret-friend language, or raw transcript export.
```

### 1.3 Xiaobaihu visual design ChatGPT session

A separate Xiaobaihu visual design session may own character image/style exploration and visual asset generation direction.

Responsibilities:

```text
1. character appearance refinement;
2. visual style consistency;
3. image/asset generation prompts;
4. animation-state visual tone suggestions;
5. keeping Xiaobaihu warm, soft, child-friendly, and non-addictive.
```

The master session remains responsible for product constraints around visual states, for example:

```text
1. jumping_happy must not become a reward or retention animation;
2. sleepy is for low-stimulation closing, not keeping the child chatting;
3. safety/privacy visuals should be calm, not scary;
4. no new assets should be integrated unless a code task explicitly allows it.
```

The code agent only integrates visual assets when a task document explicitly allows asset work.

---

## 2. QA cadence and APK testing policy

Real-device QA is essential, but it is not the same thing as daily development progress.

Current practical constraint:

```text
The product owner may only be able to test APKs at night. Daytime development should continue on scoped tasks instead of waiting idly for device feedback.
```

Therefore:

```text
1. APK/device QA should usually validate meaningful batches, not every tiny code change.
2. Lack of daytime Redmi K60 / Honor Pad 5 testing should be recorded as NOT_RUN, not treated as a reason to stop all development.
3. Automated tests and code review can pass a task for code-quality purposes while real-device QA remains pending.
4. Do not claim real-device QA passed without actual device evidence.
5. Do not let packaging/smoke loops consume the whole roadmap unless the current batch is specifically a QA package task.
```

Preferred cadence:

```text
1. Continue small focused implementation tasks during the day.
2. Accumulate device-relevant changes into a coherent batch.
3. Build/test APK when a meaningful batch is ready.
4. Run night device QA when the product owner is available.
5. Feed concrete device findings into the next scoped correction task.
```

This means Task 24 / family-beta QA package should validate Tasks 21-23 together unless a severe blocker appears earlier.

---

## 3. Forward-motion rule

The project has a large known optimization backlog. Short-term fixes must not trap the project in place.

The master session should always maintain two layers of thinking:

```text
1. immediate task review: verify current code facts and correct real defects;
2. forward roadmap: keep identifying the next product-improving task.
```

The project should not spend many cycles polishing one small area while major known work is waiting.

Near-term priority sequence after Task 21:

```text
1. Task 22 — Xiaobaihu runtime visual transition throttle / anti-flicker.
2. Task 23 — show-and-tell v3 visible quality.
3. Task 24 — family-beta QA package / APK build / night device QA.
```

After those, the master session should revisit the larger roadmap docs rather than inventing priorities from scratch:

```text
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
```

If the next product direction is ambiguous, the master session should ask the product owner targeted questions instead of letting implementation agents make design decisions.

---

## 4. Review discipline

Every development submission should still be reviewed in order:

```text
1. sync GitHub main;
2. compare against the task base commit;
3. check file scope first;
4. inspect high-risk implementation files;
5. inspect tests;
6. separate code-review pass/fail from real-device QA status;
7. then decide the next task.
```

Do not accept “done” based only on a developer summary.

Do not block all follow-up work merely because device QA is pending, unless the unresolved symptom could make the next code task invalid.

---

## 5. Practical examples

### Good behavior

```text
Task 22 finishes runtime anti-flicker tests during the day.
No physical device is available.
Master reviews code and test scope, marks device QA as NOT_RUN, then continues preparing Task 23.
At night, product owner tests a batch APK covering Tasks 21-23.
Concrete device findings become narrow correction tasks.
```

### Bad behavior

```text
Development stops all day because APK testing can only happen at night.
A code agent rewrites prompt wording while implementing Android animation timing.
A visual asset task adds new mascot frames while runtime anti-flicker is still unstable.
A QA task expands into auth/TTS/ASR refactors without explicit task scope.
```

---

## 6. Standing instruction for future master sessions

Future master sessions should preserve this operating model:

```text
The master session is the product/design/planning/review owner.
Code agents are scoped implementers.
The Xiaobaihu visual design session handles character visual exploration.
APK/device QA validates batches and should not halt daytime progress.
The roadmap should keep moving; use known optimization docs to choose the next product-improving task.
```
