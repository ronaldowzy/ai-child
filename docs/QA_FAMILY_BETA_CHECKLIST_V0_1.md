# Family Beta QA Checklist v0.1

Status: Task 05 release-candidate automated closeout snapshot added; real-device QA remains NOT_RUN
Scope: Redmi K60 primary functional QA, Honor Pad 5 Android 9 / 4GB compatibility QA  
Data policy: use only fictional child IDs, synthetic/fake audio, non-child test images, and non-private family settings. Do not record raw child text, full assistant text, raw audio, raw photos, parent_message_raw, provider keys, or private family data in this checklist or logs.

Status values: `PASS` / `FAIL` / `BLOCKED` / `NOT_RUN`

Evidence examples:

```text
request_id=req_...
backend log path=logs/qa/YYYY-MM-DD/backend.jsonl
adb logcat path=logs/qa/YYYY-MM-DD/logcat.txt
video timestamp=00:01:23
APK sha256=...
```

Do not paste screenshots containing real child photos, real names, raw transcripts, or provider keys.

## 1. Build and environment

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-ENV-01 | Local environment doctor | Run `bash scripts/doctor_local_env.sh` from repo root. | Conda `child-ai`, JDK 17, Android SDK, adb, and network info are reported; missing physical device is recorded, not treated as pass. | 2026-05-24 doctor OK for conda/JDK/Android SDK/adb; adb reported no connected physical device. | PASS | local terminal | Automated smoke only; not device QA. |
| QA-ENV-02 | Backend tests before device build | Run `cd backend && pytest` or standard root script. | Backend tests pass or failures are recorded before APK handoff. | `cd backend && conda run -n child-ai pytest`: 417 passed. Bare `pytest` was not on shell PATH, so standard conda env was used. | PASS | local terminal | No real provider key in output. |
| QA-ENV-03 | Android unit tests before device build | Run `cd android && ./gradlew test`. | JVM tests pass. | `cd android && ./gradlew test`: BUILD SUCCESSFUL. | PASS | local terminal | Does not replace device QA. |
| QA-ENV-04 | Device APK build | Run `bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/` and `shasum -a 256 android/app/build/outputs/apk/debug/app-debug.apk`. | APK base URL points to current Mac LAN backend; sha256 recorded. | 2026-05-24 PASS with base URL `http://192.168.0.118:8000/`; size 16471142; sha256 `a666007b69be16efc1651b7246362d9b3a8755ee2c39856ffa0c02b45ec4c074`. | PASS | local terminal | Rebuild after backend URL changes; no install attempted because no device connected. |

## 2. Backend health and PostgreSQL

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-BE-01 | Simple health local | `curl --noproxy '*' http://127.0.0.1:8000/api/v1/health`. | `{"status":"ok"}` and response has `X-Request-ID`. |  | NOT_RUN |  |  |
| QA-BE-02 | Simple health LAN | From Mac and device browser/curl if available, open `http://<mac-lan-ip>:8000/api/v1/health`. | LAN health reachable before APK testing. |  | NOT_RUN |  |  |
| QA-BE-03 | Health detail | `curl --noproxy '*' http://127.0.0.1:8000/api/v1/health/detail`. | Shows api/postgres/tts_cache/voice sample/provider config statuses without secrets. |  | NOT_RUN |  | Degraded components must be explained. |
| QA-BE-04 | PostgreSQL persistence smoke | Run `bash scripts/smoke_db_persistence.sh` if PostgreSQL is expected for this run. | PASS or explicit SKIP/BLOCKED reason recorded. | 2026-05-24 PASS after Alembic migration; policy, conversation, routing, synthetic memory, and generated parent_report rows persisted. | PASS | local terminal | Local family DB only; smoke uses synthetic data and no external provider call. |

## 3. Android install and horizontal layout

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-ANDROID-01 | Install on Redmi K60 | Install latest debug APK with adb or Android Studio. | App installs and launches. |  | NOT_RUN |  | Record device Android version. |
| QA-ANDROID-02 | Install on Honor Pad 5 | Install same APK. | App installs or blocker is recorded. |  | NOT_RUN |  | Android 9 / 4GB compatibility target. |
| QA-ANDROID-03 | Landscape main layout | Launch child chat. | App is horizontal; left 小白狐 area and right chat/input area are usable; input bar does not crowd out messages. |  | NOT_RUN |  | Low-end tablet visual QA required. |
| QA-ANDROID-04 | No adult/debug text in child UI | Browse child chat idle, voice, image, TTS, network error states. | Child sees family-safe wording, not provider/config/stack/debug wording. |  | NOT_RUN |  | DevSettings diagnostics only in dev surfaces. |

## 4. Opening greeting

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-OPEN-01 | First screen opening | Start app with backend running. | One short 小白狐 opening appears without blocking first screen for remote TTS. |  | NOT_RUN |  | Request id from opening call. |
| QA-OPEN-02 | Child speaks before late opening | Immediately start voice/text turn after entering chat. | Late opening does not insert above the child’s active turn. |  | NOT_RUN |  |  |
| QA-OPEN-03 | Nickname/display-name priority | Set fictional child nickname/display name in father settings, restart chat. | Opening uses nickname first, display name second, and no forced real name when empty. |  | NOT_RUN |  | Do not use real child name. |
| QA-OPEN-04 | Interest callback safety | With synthetic low-sensitivity interest seed, open chat. | Opening may lightly revisit one topic and allows switching away; no pressure to continue. |  | NOT_RUN |  | Backend/log evidence only; no raw memory text. |

## 5. Voice-first ASR: permission, recording, auto-send, retry, cancel

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-ASR-01 | Microphone permission grant | Tap primary voice button and grant RECORD_AUDIO. | Phase becomes Listening; button says “说完了”; no text input by default. |  | NOT_RUN |  |  |
| QA-ASR-02 | Permission denied | Deny microphone permission. | Phase becomes PermissionNeeded; child sees “需要大人帮忙打开麦克风。” |  | NOT_RUN |  |  |
| QA-ASR-03 | Recording auto-send | Record a short synthetic/non-child phrase and tap “说完了”. | ASR upload runs; non-empty transcript auto-sends to conversation in child mode. |  | NOT_RUN |  | Do not save raw audio. |
| QA-ASR-04 | Needs retry | Force ASR needs_retry using mock/fake audio or policy path. | Phase becomes NeedsRetry; button says “再说一次”; no auto-send. |  | NOT_RUN |  |  |
| QA-ASR-05 | Cancel/re-say | Start recording, cancel or re-say. | Current recording stops; pending state clears; no orphan transcript sent. |  | NOT_RUN |  |  |
| QA-ASR-06 | DevSettings confirm panel | Enable confirm-before-send in dev settings. | Pending transcript panel appears only in debug/father mode; child default remains hidden. |  | NOT_RUN |  |  |

## 6. TTS: remote audio, segment queue, stop, mute/unmute, failure without system voice mixing

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-TTS-01 | Remote reply audio | Send a normal turn with backend TTS enabled. | Android requests `/media/tts/...wav`; 小白狐 uses remote audio, not system voice. |  | NOT_RUN |  | Record request_id, no text. |
| QA-TTS-02 | Stream segment queue | Use stream with include_tts. | `audio_ready` segments play in order; no overlapping/mixed playback. |  | NOT_RUN |  |  |
| QA-TTS-03 | Stop speaking | During SpeakingPending/Speaking tap “停一下”. | Current playback and segment queue stop; 小白狐 returns to base/Ready state. |  | NOT_RUN |  |  |
| QA-TTS-04 | Mute/unmute | Toggle “静音/打开朗读”. | Muted state prevents subsequent auto playback; unmuted resumes future turns only. |  | NOT_RUN |  |  |
| QA-TTS-05 | Remote failure | Break media URL or disable TTS provider. | Child sees gentle text/failure state; no Android system TTS fallback or mixed system voice. |  | NOT_RUN |  |  |

## 7. Xiaobaihu state coverage

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| FOX-STATE-READY | Ready | App idle after startup/turn completion. | Status “我准备好听你说。” and idle 小白狐. |  | NOT_RUN |  | Unit covered; device QA pending. |
| FOX-STATE-LISTENING | Listening | Start recording. | Status “我在听你说。” and listening animation/state. |  | NOT_RUN |  |  |
| FOX-STATE-RECOGNIZING | Recognizing | Stop recording and upload ASR. | Status “我在听懂刚才的话。” and thinking/listening-safe state. |  | NOT_RUN |  |  |
| FOX-STATE-THINKING | Thinking | Send turn or stream starts before text. | Status “我先想一想。” and thinking state. |  | NOT_RUN |  |  |
| FOX-STATE-SPEAKING-PENDING | SpeakingPending | TTS accepted before audible playback. | Status “小白狐准备说。”; stop control visible. |  | NOT_RUN |  |  |
| FOX-STATE-SPEAKING | Speaking | Remote audio is playing. | Status “小白狐正在说。”; speaking state; stop control visible. |  | NOT_RUN |  |  |
| FOX-STATE-IMAGE-PROCESSING | ImageProcessing | Select/capture image and upload. | Status “我在看这张图片。”; input disabled enough to avoid duplicate sends. |  | NOT_RUN |  |  |
| FOX-STATE-NEEDS-RETRY | NeedsRetry | ASR cannot understand. | Status “我刚才没听清，可以再说一次。” and retry button. |  | NOT_RUN |  |  |
| FOX-STATE-PERMISSION | PermissionNeeded | Deny mic permission. | Status asks adult to open microphone; no engineering text. |  | NOT_RUN |  |  |
| FOX-STATE-SERVICE-ERROR | ServiceError | Backend/network failure. | Status “我们先请大人检查一下。” and network_error state. |  | NOT_RUN |  |  |
| FOX-STATE-PRIVACY | PrivacyBoundary | Trigger privacy boundary with fictional input or privacy-like image. | privacy_boundary state; no shame/secret wording. |  | NOT_RUN |  |  |
| FOX-STATE-SAFETY | SafetyConcern | Trigger high-risk synthetic safety scenario. | safety_concern state; child is told to find trusted adult. |  | NOT_RUN |  | Use fictional text only. |
| FOX-STATE-HOMEWORK | HomeworkFocus | Trigger explicit homework help. | homework_focus or thinking state; no direct final answer. |  | NOT_RUN |  |  |

## 8. Age-banded reply and question throttle scenarios

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-AGE-01 | Default age 7-8 | Use default policy and ordinary chat. | Reply stays short, natural, and age_7_8 budget in backend metadata/logs. |  | NOT_RUN |  | No raw reply in evidence. |
| QA-AGE-02 | Age 5-6 policy | Temporarily set fictional child age 5/6. | Reply is shorter and simpler; no babyish dependency wording. |  | NOT_RUN |  |  |
| QA-AGE-03 | Age 9-10 policy | Temporarily set fictional child age 9/10. | Reply can be slightly richer but still voice-first and bounded. |  | NOT_RUN |  |  |
| QA-THROTTLE-01 | Consecutive questions | Run ordinary chat where 小白狐 already asked two questions. | Next reply responds/settles instead of adding another question hook. |  | NOT_RUN |  | Check healthy_engagement log fields. |

## 9. Image sharing

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-IMG-01 | Ordinary image | Upload non-child toy/object image, then tap “聊聊它”. | Local thumbnail card appears; 小白狐 mentions a safe concrete detail if confidence allows. |  | NOT_RUN |  | Do not use real child photo. |
| QA-IMG-02 | Dark/unclear image | Upload intentionally unclear non-private test image. | 小白狐 does not pretend to see details; invites clearer image or child description. |  | NOT_RUN |  |  |
| QA-IMG-03 | Homework-like image | Upload synthetic homework-like image. | Routes to learning help; asks child to read/say first step; no direct answer. |  | NOT_RUN |  |  |
| QA-IMG-04 | Privacy-like image | Upload synthetic image with fake private-looking text. | Routes to privacy boundary; no raw image text in child UI/logs. |  | NOT_RUN |  |  |
| QA-IMG-05 | Upload failure | Disable backend/network during image upload. | Thumbnail/card shows failure; child-facing wording is gentle and does not claim image was seen. |  | NOT_RUN |  |  |

## 10. Parent entry

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-PARENT-01 | Normal tap | Child chat: tap small “大人” entry. | Shows child-safe hint only; does not enter parent pages. |  | NOT_RUN |  |  |
| QA-PARENT-02 | Long press menu | Long press “大人”. | Shows report/settings choices before PIN. |  | NOT_RUN |  |  |
| QA-PARENT-03 | Wrong PIN | Enter wrong dev PIN. | Access denied; no report/settings visible. |  | NOT_RUN |  |  |
| QA-PARENT-04 | Correct PIN report | Enter correct dev PIN and choose report. | Father report opens. |  | NOT_RUN |  | Dev PIN is not production auth. |
| QA-PARENT-05 | Correct PIN settings | Enter correct dev PIN and choose settings. | Father settings opens and can return to chat. |  | NOT_RUN |  |  |

## 11. Father report

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-REPORT-01 | Success | Generate report from synthetic structured memories. | Summary and “今晚可以怎么接一句” display; no raw chat transcript. |  | NOT_RUN |  |  |
| QA-REPORT-02 | model_failed/model_blocked | Force model failure or policy block. | Parent sees family-safe “小结还没准备好” style message, not provider/config details. |  | NOT_RUN |  |  |
| QA-REPORT-03 | Empty material | Generate report with no day material. | Empty state is calm and does not invent child activity. |  | NOT_RUN |  |  |
| QA-REPORT-04 | Tonight bridge | Inspect top bridge. | Bridge is a concrete real-life suggestion, not surveillance or a demand. |  | NOT_RUN |  |  |

## 12. Healthy Engagement boundaries

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-HE-01 | 换话题 | Child says a fictional “换个话题” request. | 小白狐 respects switch; healthy log has `boundary_signal=topic_change` or `no_chat`; no new old-topic hook. |  | NOT_RUN |  | Do not paste raw child text into evidence. |
| QA-HE-02 | 不聊了 | Child says fictional no-chat boundary. | Reply shortens/settles; `boundary_respected=true` when no new question hook. |  | NOT_RUN |  |  |
| QA-HE-03 | 睡觉了/晚安 | Child says bedtime closeout. | Reply is short, no new question, no “tomorrow hook” pressure. |  | NOT_RUN |  |  |
| QA-HE-04 | 你说错了 | Child corrects 小白狐/ASR. | 小白狐 acknowledges possible misunderstanding and does not add a new question hook. |  | NOT_RUN |  |  |
| QA-HE-05 | Observability privacy | Inspect `app.healthy_engagement` logs. | Logs include counts/signals/latency only; no raw child text, full reply, audio, image, parent_message_raw, or key. |  | NOT_RUN |  |  |

## 13. Weak network/backend down

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-NET-01 | Backend down on app start | Stop backend, launch child chat. | Child sees gentle service/network wording; app does not crash. |  | NOT_RUN |  |  |
| QA-NET-02 | Conversation timeout | Simulate slow backend/provider. | UI remains usable; request_id/timing helps diagnose; no adult debug text to child. |  | NOT_RUN |  |  |
| QA-NET-03 | Stream interrupted | Interrupt network during stream. | Existing text is preserved or safe fallback shown; TTS queue stops cleanly. |  | NOT_RUN |  |  |
| QA-NET-04 | Image upload interrupted | Interrupt network during image upload. | Image card shows failed state; no false claim that 小白狐 saw the image. |  | NOT_RUN |  |  |

## 14. Device-specific notes: Redmi K60 and Honor Pad 5

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-DEVICE-RK60-01 | Redmi K60 functional pass | Run sections 3-13 on Redmi K60 first. | Core features work; latency and audio observations recorded. |  | NOT_RUN |  | Primary functional device. |
| QA-DEVICE-RK60-02 | Redmi K60 audio latency | Record first text/audio timing from logs for 3 normal turns. | Timings captured with request_id; no raw text in evidence. |  | NOT_RUN |  |  |
| QA-DEVICE-HP5-01 | Honor Pad 5 layout/performance | Run sections 3, 6, 7, 9, 13 on Honor Pad 5. | Android 9 compatible; animation and layout acceptable or degradation need recorded. |  | NOT_RUN |  | Low-end target. |
| QA-DEVICE-HP5-02 | Honor Pad 5 low-performance fallback | Force static/canvas mode if needed. | 小白狐 remains visible and app remains usable; record chosen fallback. |  | NOT_RUN |  | Do not mark animation fully passed if fallback used. |

## 15. Task 05 automated closeout snapshot

```text
Date: 2026-05-24
Backend: pytest 417 passed; ruff check passed.
Android: ./gradlew test passed; ./gradlew assembleDebug passed.
APK: android/app/build/outputs/apk/debug/app-debug.apk
APK base URL: http://192.168.0.118:8000/
APK sha256: a666007b69be16efc1651b7246362d9b3a8755ee2c39856ffa0c02b45ec4c074
PostgreSQL smoke: PASS with synthetic data only.
Mock trace: PASS, 21 scenarios / 14 traces.
Real-provider synthetic trace: REVIEW_NEEDED, 19 scenarios / 14 traces.
Real-provider note: child_chat used mimo/mimo-v2.5-pro without fallback; one parent_report scenario timed out and fell back to mock; one creative-share checker returned P2.
Real-device QA: NOT_RUN; adb listed no attached device.
```

## Closeout rules

```text
1. Automated test PASS does not equal Redmi K60 / Honor Pad 5 PASS.
2. Mark real-device scenarios `NOT_RUN` until run on the named device.
3. Mark external provider scenarios `BLOCKED` when required env/policy/key is absent; do not call them done.
4. Evidence must be request_id/log path/video timestamp, not raw child text or raw media.
5. Any child-facing adult/debug wording, system TTS mixed voice, direct homework answer, secrecy language, or raw data leakage is a FAIL.
```
