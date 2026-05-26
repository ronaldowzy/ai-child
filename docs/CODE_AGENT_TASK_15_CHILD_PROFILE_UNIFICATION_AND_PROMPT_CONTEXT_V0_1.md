# CODE_AGENT_TASK_15_CHILD_PROFILE_UNIFICATION_AND_PROMPT_CONTEXT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: product architecture advancement  
Goal: unify registration profile and parent settings into one child profile model, then feed it consistently into prompts, opening, memory, topic suggestions, and parent report.

---

## 0. Why this task

Current problem observed by product owner:

```text
1. Parent fills child information during registration.
2. Parent later opens 家长设置 and sees/edits child information there.
3. These two surfaces are not yet truly one unified data model and field set.
4. Child gender is missing.
5. Child profile is still too thin; it lacks standardized selectable traits such as personality/communication style.
6. These attributes are not consistently guaranteed as prompt context for the model.
```

This must be fixed before further personalization work. Otherwise opening, topic suggestions, relationship memory, and parent report will keep using partial or inconsistent child data.

---

## 1. Product direction

Use one parent-operated child profile.

The child profile is not a personality label or prediction system. It is parent-provided context to help Xiaobaihu speak more appropriately and avoid wrong assumptions.

Rules:

```text
1. Registration and 家长设置 must edit the same child profile fields.
2. 家长设置 is the long-term canonical editing surface.
3. Registration can collect a smaller required subset, then 家长设置 can complete optional details.
4. Gender/call preference must not create stereotypes.
5. Personality/temperament options must be support-oriented, not fixed labels.
6. All profile fields used in prompts must be rendered as internal context, not spoken directly to the child.
7. Do not let child manage profile fields.
```

---

## 2. Canonical child profile fields v0.1

Implement or document a canonical profile object. Exact storage can use existing `ParentPolicy.communication_preferences` if that is least disruptive, but code should expose a single typed model/helper.

Required / strongly encouraged fields:

```text
child_nickname: 小名 / 希望小白狐怎么叫孩子
child_display_name: 显示名，可选
child_age: 5-10
child_grade: 年级，可选
child_gender: boy | girl | prefer_not_to_say | custom | unknown
child_call_preference: 称呼/代词/称呼偏好，可选
child_interests: list[str]
topic_boundaries: list[str]
```

New standardized selectable fields:

```text
child_temperament: list enum, optional
  - warms_up_slowly        慢热，需要一点时间
  - expressive             爱表达，话比较多
  - concise                说话短，需要小选择
  - imaginative            爱想象/编故事
  - active                 喜欢运动和动手
  - sensitive_to_pressure  不喜欢被追问或催促
  - easily_frustrated      遇到困难容易急
  - curious                爱问为什么

support_style_preferences: list enum, optional
  - offer_two_choices          多给二选一
  - ask_fewer_questions        少追问
  - encourage_gently           多温和鼓励
  - slow_down_explanations     解释慢一点
  - use_shorter_sentences      句子短一点
  - invite_show_and_tell       多鼓励展示作品/物品
  - avoid_competition_framing  少用输赢/排名框架

learning_support_preferences: list enum, optional
  - hint_first                 先提示，不直接给答案
  - ask_what_child_knows       先问孩子知道什么
  - use_examples               用例子解释
  - keep_homework_short        作业帮助要短
```

Free text fields:

```text
parent_message_raw: 家长寄语 / 补充说明
profile_notes: 可选短备注，<= 500 chars; not required in v0.1 if parent_message_raw already covers it
```

Do not add sensitive categories such as diagnosis, IQ, family income, exact school name, home address, medical history, or psychological labels.

---

## 3. Backend design requirements

### 3.1 Single profile helper/schema

Add a typed schema/helper, for example:

```text
backend/app/domain/schemas/child_profile.py
```

Suggested public functions:

```python
ChildProfile
ChildProfileUpdate
child_profile_from_parent_policy(policy)
child_profile_preferences_from_input(input, existing)
render_child_profile_for_prompt(profile)
```

Exact names can vary, but there must be one canonical path for:

```text
1. auth registration input;
2. parent settings update;
3. prompt rendering;
4. opening context;
5. topic seed/quick action context;
6. relationship memory context;
7. parent report context.
```

### 3.2 Storage

Prefer using existing `ParentPolicy` fields plus `communication_preferences` to avoid migration if possible.

If using `communication_preferences`, store canonical keys:

```text
child_age
child_grade
child_gender
child_call_preference
child_interests
topic_boundaries
child_temperament
support_style_preferences
learning_support_preferences
child_profile_schema = "child_profile_v0_2"
```

Registration should initialize the same fields. Parent settings should edit the same fields. `/auth/me` should return the same profile view.

### 3.3 Prompt context

`PromptManager._render_child_profile()` must include the canonical profile fields in a clear internal section:

```text
孩子画像（内部使用，不要直接说给孩子）：
- 年龄/年龄段
- 年级
- 性别/称呼偏好：只用于尊重称呼，不用于兴趣/能力/性格推断
- 兴趣
- 不想聊/少追问主题
- 沟通特点：例如慢热、说话短、爱想象
- 支持方式：例如多给二选一、少追问、句子短一点
- 学习支持方式：例如先提示、用例子解释
```

Do not expose raw `parent_message_raw` as child-visible content.

### 3.4 Opening/topic/report integration

Update the services that currently read partial profile/preferences so they use the unified helper:

```text
opening_service
topic_seed_service / quick_action_service
conversation_memory_hooks / relationship_memory
parent_report_service
```

Do not overfit behavior. The profile should guide style, not decide the child forever.

---

## 4. Android requirements

### 4.1 Registration screen

Registration should collect a minimal subset:

```text
username
password
child_nickname
child_age
optional child_gender or prefer_not_to_say
```

Keep registration simple. Do not make first use heavy.

### 4.2 家长设置 screen

家长设置 should be the canonical full profile editing surface. It should show/edit:

```text
小名
显示名
年龄
年级
性别/不填写/自定义称呼偏好
孩子最近喜欢的话题
不想聊/少追问的话题
性格/表达特点 multi-select
支持方式 multi-select
学习支持方式 multi-select
家长寄语
本周目标
```

UI can be simple: chips, checkboxes, dropdowns, comma-separated fields where faster. Do not overbuild.

### 4.3 Consistency

After registration:

```text
1. entering 家长设置 should show the same values;
2. saving 家长设置 should update `/auth/me` profile after refresh/relogin if applicable;
3. chat/opening should use saved profile context.
```

---

## 5. Allowed files

Backend:

```text
backend/app/domain/schemas/auth.py
backend/app/domain/schemas/parent_policy.py
backend/app/domain/schemas/child_profile.py
backend/app/services/auth_service.py
backend/app/services/parent_policy_service.py
backend/app/services/prompt_manager.py
backend/app/services/opening_service.py
backend/app/services/topic_seed_service.py
backend/app/services/quick_action_service.py
backend/app/services/relationship_memory.py
backend/app/services/parent_report_service.py
backend/app/tests/**/*auth*
backend/app/tests/**/*parent_policy*
backend/app/tests/**/*prompt*
backend/app/tests/**/*child_profile*
```

Android:

```text
android/app/src/main/java/com/childai/companion/data/auth/*
android/app/src/main/java/com/childai/companion/data/parent/*
android/app/src/main/java/com/childai/companion/ui/auth/*
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/test/java/com/childai/companion/**/*Auth*
android/app/src/test/java/com/childai/companion/ui/parent/*
```

Docs:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
```

Avoid DB migration unless absolutely necessary.

---

## 6. Do not do

```text
1. Do not add family/multi-child/multi-guardian accounts.
2. Do not add production compliance flows.
3. Do not add raw transcript export.
4. Do not use gender to infer hobbies, colors, ability, personality, or behavior.
5. Do not label the child as fixed personality type in child-facing reply.
6. Do not add diagnosis/medical/psychological labels.
7. Do not modify TTS provider/fallback, ASR, image upload transport, Android navigation, or mascot animation engine.
```

---

## 7. Tests

Add/modify tests for:

```text
1. Register with nickname/age/gender initializes the same profile visible in parent settings/auth me.
2. Parent settings updates the same canonical profile fields.
3. PromptManager renders age, gender/call preference, temperament, support preferences, interests, topic boundaries as internal context.
4. Gender/call preference text explicitly says not to infer interests/ability/personality from gender.
5. Opening/topic suggestions use profile interests and support preferences.
6. Topic boundaries filter topic suggestions.
7. Profile defaults are safe when fields are missing.
```

Minimum commands:

```bash
cd backend && pytest backend/app/tests/test_auth_api.py backend/app/tests/test_prompt_manager.py backend/app/tests/test_parent_policy*.py backend/app/tests/test_topic_seed_service.py
cd backend && ruff check .
cd android && ./gradlew test
```

Report skipped tests honestly.

---

## 8. Final response required

Report:

```text
1. commit sha;
2. files changed by backend/android/docs;
3. canonical child profile schema;
4. registration -> parent settings consistency behavior;
5. prompt context example showing profile fields;
6. tests run and results;
7. confirmation that gender is not used for stereotypes;
8. confirmation no TTS/ASR/image/navigation/mascot engine work was added.
```
