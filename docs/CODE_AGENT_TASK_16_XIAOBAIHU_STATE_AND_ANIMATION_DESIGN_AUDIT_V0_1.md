# CODE_AGENT_TASK_16_XIAOBAIHU_STATE_AND_ANIMATION_DESIGN_AUDIT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: specialist audit/design task, not broad implementation  
Goal: audit whether the designed Xiaobaihu visual states and dynamic animations are actually used, then prepare the next animation/state optimization plan.

---

## 0. Why this task

The project previously produced many Xiaobaihu visual/animation states. Current docs say the Android asset manifest declares 11 dynamic states:

```text
safety_concern
privacy_boundary
network_error
speaking
thinking
listening
homework_focus
calm
sleepy
jumping_happy
idle
```

But it is unclear whether all are triggered by real business events. Some states may be resource-ready but not actually used. Product owner wants this as a separate design topic.

This task must not start by generating new art assets. First audit coverage.

---

## 1. Required reading

```text
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/mascot/*
android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json
```

---

## 2. Audit goals

Produce a current coverage table answering:

```text
1. Which animation assets exist?
2. Which MascotState enum/state exists?
3. Which FoxMood/FoxMotion maps to each state?
4. Which ChildTurnUiPhase or backend reply emotion/agent_motion triggers it?
5. Which states are used in normal child chat?
6. Which states are only used in rare safety/privacy/homework/network scenes?
7. Which states are resource_ready_but_not_triggered?
8. Which states are missing from business logic?
9. Which states need new design before implementation?
```

---

## 3. Required deliverable

Create/update a design doc, for example:

```text
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
```

It must include:

```text
1. Executive summary.
2. Current asset manifest inventory.
3. Current code mapping inventory.
4. Current business trigger inventory.
5. State coverage matrix.
6. Gaps and risks.
7. Recommended state model v2.
8. Recommended next implementation task.
9. QA scenarios for Redmi K60 / Honor Pad 5.
```

---

## 4. State coverage matrix format

Use a table like:

```text
State ID | Asset exists | MascotState exists | FoxMood/FoxMotion | Trigger path | Frequency | Current status | Recommendation
```

Status values:

```text
implemented_and_triggered
implemented_rare_scene
resource_ready_but_not_triggered
missing_mapping
missing_asset
needs_design
```

---

## 5. Product design guidance

Do not simply map every tiny backend scene to a new animation. Xiaobaihu should feel alive but not noisy.

Recommended v2 state layers:

```text
Base attention state:
- idle / ready
- listening
- thinking
- speaking
- looking_at_image
- resting

Emotional overlay:
- warm
- curious
- encouraging
- calm
- concerned
- sleepy

Boundary/safety overlay:
- privacy_boundary
- safety_concern
- network_error
- homework_focus
```

Avoid:

```text
1. too many rapid animation switches;
2. emotional overacting;
3. reward-like jumping for every small reply;
4. states that encourage more use or dependence;
5. child-facing scary safety visuals.
```

---

## 6. Allowed files

This is primarily a documentation/audit task.

Allowed:

```text
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
android/app/src/test/java/com/childai/companion/ui/chat/*StateCoverage*  # optional, if adding a non-invasive audit test
```

Avoid code changes unless they are tests/audit only.

Do not modify:

```text
runtime mascot engine
assets
animation frames
TTS
ASR
auth
conversation backend
parent report
```

---

## 7. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. state coverage summary;
4. list of states actually triggered today;
5. list of resource_ready_but_not_triggered states;
6. recommended next implementation task;
7. confirmation no assets/runtime engine were changed.
```
