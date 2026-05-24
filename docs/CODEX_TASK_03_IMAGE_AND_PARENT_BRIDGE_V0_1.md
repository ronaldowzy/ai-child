# Codex Task 03: Image Sharing and Parent Bridge v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: coordinated implementation batch  
Recommended mode: two Codex sessions on separate branches/worktrees; if only one Codex session is available, execute Lane A first, then Lane B.

---

## 0. Why this batch

Task 01 and Task 02 have completed the first two experience foundations:

```text
1. Android child-facing interaction phase reducer.
2. voice-first TTS stop/mute closeout.
3. backend age-banded reply budget.
4. continuous-question throttle thin slice.
```

The next two highest-value family-beta experience gaps are:

```text
Lane A: “拍给小白狐看” must feel like the child was specifically seen, not just like an upload template.
Lane B: father governance must stay available but less intrusive, and father daily report must help real-life parent conversation rather than feel like a monitoring/debug report.
```

These lanes touch mostly separate areas and can run in parallel.

---

## 1. Coordination rules

### If using two Codex sessions

Use two branches:

```text
codex/e3-01-image-specific-response-thumbnail
codex/e4-01-parent-entry-report-bridge
```

Merge order:

```text
1. Merge Lane A first if it changes shared Android chat models.
2. Rebase Lane B on latest main.
3. Merge Lane B second.
```

Avoid both lanes editing the same documentation in parallel except `docs/CODEX_PROGRESS_BOARD_V0_1.md`; resolve that at merge time.

### If using one Codex session

Do this sequence:

```text
1. Implement Lane A.
2. Run backend and Android targeted tests.
3. Commit Lane A.
4. Implement Lane B.
5. Run backend and Android targeted tests.
6. Commit Lane B.
```

Do not casually mix Lane A and Lane B files.

---

## 2. Shared required reading

Before coding, read:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
```

Lane B additionally reads:

```text
backend/app/services/parent_report_service.py
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
```

---

# Lane A — Image sharing “具体看见” + local thumbnail

## A1. Goal

Make “拍给小白狐看” feel like Xiaobaihu actually saw a specific, safe detail.

Current issue:

```text
1. Android sends a text bubble “我拍了一张图片给小白狐看。” but does not show a local thumbnail/card.
2. Backend ordinary image share first response is still too template-like, often “我看到这张图啦……”.
3. The backend already has recognized_content.text / child_caption / recognized_type, but first child-facing feedback does not consistently use one concrete detail.
```

## A2. Allowed files

Backend:

```text
backend/app/services/modality_manager.py
backend/app/services/attachment_service.py
backend/app/domain/attachment.py
backend/app/domain/schemas/conversation.py
backend/app/tests/**/*image*  or relevant attachment/modality tests
```

Android:

```text
android/app/src/main/java/com/childai/companion/data/attachment/*
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
android/app/src/test/java/com/childai/companion/data/attachment/*
```

Docs:

```text
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
android/README.md
```

## A3. Do not do

```text
1. Do not introduce CameraX in this lane.
2. Do not store real child photos long-term in Android or backend beyond existing controlled attachment storage.
3. Do not add API keys or direct MiMo calls to Android.
4. Do not make ordinary images default to homework.
5. Do not over-trigger privacy boundary for ordinary images.
6. Do not pretend to see details not in recognized_content.
7. Do not expose raw JSON or provider diagnostics to the child.
```

## A4. Backend requirements

### A4.1 Specific first response

In `ModalityManager.decide_image_attachment`, for ordinary non-homework image share:

```text
If recognized_content.type == image_observation and recognized_content.text is non-empty:
  reply_text should include one concise, safe, concrete detail from recognized_content.text.

If confidence is low, text missing, type unsafe_unknown, or recognized text is too vague:
  reply_text should acknowledge uncertainty and ask the child to say what they want Xiaobaihu to look at.

If type privacy_sensitive:
  preserve privacy boundary behavior.

If type homework_problem or image_purpose == learning_homework:
  preserve learning scaffold and no direct answer.
```

Example styles:

```text
High confidence ordinary image:
  “我看到图里像是一个积木城堡/窗边的灯/一张画。你想先讲讲它哪里最有意思吗？”

Low confidence:
  “这张图我看得还不太清楚。你可以告诉我，你最想让我看哪里？”
```

Keep it short and TTS-friendly. Do not generate a report.

### A4.2 Detail extraction helper

Add a small helper, e.g.:

```python
def _child_visible_image_detail(recognized_content: RecognizedContent) -> str | None:
    ...
```

Rules:

```text
1. Strip labels like child_summary/context_summary/图片描述.
2. Limit to roughly 35–60 Chinese chars.
3. Prefer first sentence or first clause.
4. Do not include private-looking long numbers, phone numbers, addresses, or school/class labels in the detail.
5. If uncertain, return None.
```

### A4.3 Tests

Add backend tests:

```text
1. image_observation + text + confidence >= threshold -> reply includes concrete detail.
2. image_observation + low confidence -> reply says not clear and asks child what to look at.
3. privacy_sensitive -> existing privacy reply preserved.
4. homework_problem / learning_homework -> does not give answer; asks about题意/卡点.
5. detail helper strips labels and truncates safely.
```

---

## A5. Android requirements

### A5.1 Local temporary image card

When the child captures or picks an image, show a local temporary image card/message in the chat so the child can confirm what was sent.

Minimum acceptable implementation:

```text
1. Extend child image message UI model to optionally include a local preview URI or local bitmap bytes reference that is not persisted long-term.
2. For captured/gallery image, display a rounded thumbnail/card in the message list alongside “我拍了一张图片给小白狐看。”
3. If rendering actual bitmap is too much for this lane, create a visible “图片已发送给小白狐” card with file type/size and mark actual thumbnail as next QA item. But preferred: render local thumbnail.
```

Do not upload or expose the local URI to model prompts. It is only UI confirmation.

### A5.2 Upload failure still clear

If upload fails, keep the child-friendly failure message. Do not lose the image card; it may remain with a subtle failed state if easy, or append a friendly failure bubble.

### A5.3 Tests

Add/update Android tests:

```text
1. submitCapturedPhoto appends child message with image preview/card metadata.
2. submitCapturedPhoto sets ImageProcessing phase.
3. upload failure keeps gentle child-facing message.
4. no raw local path is sent in backend API payload beyond existing multipart upload path.
```

If Compose screenshot tests are not available, use model-level tests for message metadata.

---

## A6. Lane A acceptance criteria

```text
1. Ordinary image first response includes a concrete recognized detail when safe and confident.
2. Low-confidence image does not pretend to know.
3. Homework and privacy routes remain safe.
4. Android chat shows a child-visible image confirmation card/thumbnail after capture/gallery selection.
5. Existing attachment_id pending image continuation still works.
6. Tests added/updated for backend and Android.
7. Redmi K60 / Honor Pad 5 real camera/gallery QA remains marked pending unless actually tested.
```

---

# Lane B — Parent entry deemphasis + father report real-life bridge

## B1. Goal

Father governance should be clear for adults but not dominate the child’s chat. Father Daily Report should help father say something concrete in real life, not read like surveillance or a developer report.

Current issue:

```text
1. Child chat top bar still shows large “父亲日报 / 父亲设置 / 长按进入”.
2. Father report failure text still contains engineering concepts like backend/model config in some states.
3. Report sections exist, but the top does not yet strongly prioritize “今晚可以怎么接一句”.
```

## B2. Allowed files

Android parent entry:

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
```

Android parent report:

```text
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportViewModel.kt
android/app/src/main/java/com/childai/companion/data/parent/*
android/app/src/test/java/com/childai/companion/ui/parent/*
android/app/src/test/java/com/childai/companion/data/parent/*
```

Backend parent report:

```text
backend/app/domain/parent_report.py
backend/app/services/parent_report_service.py
backend/app/repositories/parent_report_repository.py
backend/app/tests/**/*parent_report*
```

Docs:

```text
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
android/README.md
```

## B3. Do not do

```text
1. Do not remove parent report/settings access.
2. Do not remove long-press + PIN protection.
3. Do not display full child transcripts in the report.
4. Do not add monitoring language like “孩子今天说了 X 次”.
5. Do not expose backend/model/provider/debug wording in family-facing UI by default.
6. Do not build a full account/auth system.
```

## B4. Parent entry deemphasis requirements

Replace the two prominent child top-bar buttons with a lighter adult area.

Minimum acceptable UX:

```text
1. Top bar child-facing title remains “小白狐” and status text remains phase-driven.
2. Parent access becomes one small “给大人的角落” / “大人” / subtle icon-like button.
3. Normal tap shows gentle hint: “这是给大人看的，请让大人长按进入。”
4. Long press opens parent gate or reveals choices for “父亲日报 / 父亲设置”.
5. After PIN success, father can still enter both report and settings.
```

Implementation option:

```text
Option A: One compact parent button opens a long-press target selector after PIN.
Option B: One compact button, long-press report by default; after hint or simple menu, settings still accessible.
```

Prefer Option A if low risk. Do not overbuild.

Tests:

```text
1. Normal tap does not navigate to parent pages.
2. Hint text is family-friendly.
3. Long press path still invokes parent gate for report/settings.
4. Child top bar no longer renders both large labels by default.
```

If current UI tests cannot simulate long press, add pure state/helper tests and preview comments.

## B5. Father report “tonight one sentence” requirements

### B5.1 Backend/domain

Add a field if compatible, e.g.:

```python
tonight_parent_bridge: str | None
```

or Android-only derived field if schema migration is too risky. Preferred: optional backend/domain field with backward compatibility.

Generated report should produce a short, non-monitoring parent bridge:

```text
“今晚可以轻轻问：‘你今天说那个越野泥坑，最难的是哪一段？’ 如果孩子不想说，就换成一起看看他的鞋/衣服有没有需要整理。”
```

Rules:

```text
1. It must be a realistic parent sentence/action.
2. It must not quote sensitive child content verbatim.
3. It must not encourage interrogation.
4. It must include “如果孩子不想说，不追问/换轻松方式” when appropriate.
5. Empty material report should say not enough material and advise not to追问.
```

If model-generated report parser cannot parse new field reliably, implement fallback derivation from `suggested_parent_actions[0]` or deterministic report material, but expose a stable Android UI concept.

### B5.2 Android UI

At the top of ParentReportScreen, above “今日整体摘要”, add a section/card:

```text
今晚可以怎么接一句
<tonight_parent_bridge or derived sentence>
```

For failure/loading/empty material:

```text
1. Failure text: “今天的小结还没准备好，请稍后再试。”
2. Do not mention backend/model/provider by default.
3. Developer diagnostic can be omitted in this lane or hidden under DevSettings if already available.
```

### B5.3 Tests

Backend tests:

```text
1. deterministic fallback report includes bridge sentence/action for no-material case.
2. model parse accepts optional tonight_parent_bridge if present.
3. forbidden child labels still sanitized.
4. no full transcript/evidence exposed.
```

Android tests:

```text
1. ParentReport data model parses optional tonight_parent_bridge.
2. ParentReportScreen preview/model test can render bridge card.
3. failure message does not contain backend/model/provider/config.
```

---

## B6. Lane B acceptance criteria

```text
1. Child chat top bar no longer shows two prominent “父亲日报/父亲设置” buttons by default.
2. Parent access remains available and PIN-protected.
3. Parent report family-facing failure text no longer exposes engineering wording by default.
4. Parent report shows a top bridge section: “今晚可以怎么接一句”.
5. Backend/domain or Android derivation supports bridge text without transcript exposure.
6. Empty report advises father not to interrogate the child.
7. Tests added/updated.
8. Real parent-device QA remains pending unless tested.
```

---

## 3. Documentation updates

Lane A updates:

```text
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
android/README.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Lane B updates:

```text
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
android/README.md
```

Rules:

```text
1. Do not mark true device QA as passed unless real devices were tested.
2. Mark Redmi K60 / Honor Pad 5 as pending if not tested.
3. Do not claim parent governance is production-grade auth.
4. Do not claim image recognition is always correct; keep low-confidence behavior explicit.
```

---

## 4. Test commands

Lane A should run at least:

```bash
cd backend
pytest backend/app/tests/test_*attachment* backend/app/tests/test_*image* backend/app/tests/test_*modality* || pytest
ruff check .

cd android
./gradlew test
```

Lane B should run at least:

```bash
cd backend
pytest backend/app/tests/test_parent_report* backend/app/tests/test_*parent_report* || pytest
ruff check .

cd android
./gradlew test
```

If targeted globs do not match in the current project, use the closest existing targeted tests and state exactly what ran.

---

## 5. Final response required from Codex

Codex must report:

```text
1. branch/commit sha(s),
2. which lane(s) were completed,
3. modified files,
4. test commands and exact results,
5. skipped tests or unavailable test suites,
6. remaining real-device QA items,
7. whether implementation stayed within scope,
8. any schema compatibility notes.
```
