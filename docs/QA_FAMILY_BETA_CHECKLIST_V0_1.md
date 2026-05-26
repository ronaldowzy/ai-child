# Family Beta QA Checklist v0.1

Status: Task 10 account/opening/control closeout automated snapshot added; real-device QA remains NOT_RUN
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

Do not paste screenshots containing real child photos, real names, raw transcripts, auth tokens, or provider keys.

## Task 10 QA focus

Task 10 closes out Task 09 account and personalization foundations. The next device round must explicitly cover:

```text
1. 家长创建一个孩子账号、登录、重启保持登录、手动退出。
2. 家长设置和家长日报使用当前登录账号 child_id，默认不再要求开发 PIN。
3. Opening v2 个性化但不阻塞首屏 Ready；孩子先开口时迟到 opening 不插入。
4. CS/game/sports 短答时 conversation_control soft_shift 自然给换题机会，高参与时不强制换题。
5. Topic choices 来自后端 quick actions；Android 不展示独立硬编码恐龙/太空 fallback chips。
6. Slow opening evidence must align backend request_id, `app.opening_timing`, Android video timestamp, and no raw child text.
```

Evidence stays non-sensitive: account username can be synthetic, but do not record passwords, bearer tokens, real child names, raw transcript, raw audio, raw image, or provider key.

## Task 08 evidence collection protocol

Task 08 round 2 status: no new Redmi K60 / Honor Pad 5 video, backend `request_id`, or Android `XiaobaohuTtsTiming` logcat evidence was available in this Codex run. Lane B/C/D fixes remain skipped until a concrete device symptom is linked to evidence.

For the next real-device round, collect only non-sensitive evidence:

```text
1. Install the Task 08 APK from `android/app/build/outputs/apk/debug/app-debug.apk`.
2. Start the backend on the Mac LAN URL used at build time: `http://192.168.0.118:8000/`.
3. For one slow synthetic turn, record the backend `request_id` from response headers or backend logs.
4. Around the same turn, capture Android timing lines with:
   `adb logcat -v time | grep XiaobaohuTtsTiming`
5. Preserve backend timing log names and request_id only:
   `conversation_turn_latency`, `conversation_stream_finished`, `request_id`, `model_ms`, `tts_ms`, `first_text_ms`, `tts_started_ms`, `first_audio_ms`, `turn_total_ms`.
6. Record video timestamps such as `Redmi K60 video 00:01:23`, without uploading raw child audio, raw child photos, private names, full child transcript, full assistant reply, parent_message_raw, provider keys, DB dumps, or full signed media URLs.
```

Slow-turn classification rules:

```text
model_ms high -> model/provider generation delay.
tts_ms or first_audio_ms high -> backend TTS generation or audio_ready delay.
remote_audio_url_received to remote_audio_playback_started high -> Android download/prepare/playback delay.
remote_audio_error -> network/media playback failure.
No request_id/logcat/video -> NOT_RUN; do not guess or modify code.
```

## 1. Build and environment

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-ENV-01 | Local environment doctor | Run `bash scripts/doctor_local_env.sh` from repo root. | Conda `child-ai`, JDK 17, Android SDK, adb, and network info are reported; missing physical device is recorded, not treated as pass. | 2026-05-25 Task 10: conda/JDK/Android SDK/adb OK; LAN IP `192.168.0.118`; adb warned no connected physical Android device. | PASS | local terminal | Automated smoke only; not device QA. |
| QA-ENV-02 | Backend tests before device build | Run `cd backend && pytest` or standard root script. | Backend tests pass or failures are recorded before APK handoff. | 2026-05-25 Task 10: `bash scripts/test_backend.sh` -> 453 passed. | PASS | local terminal | No real provider key in output. |
| QA-ENV-03 | Android unit tests before device build | Run `cd android && ./gradlew test` or the standard wrapper. | JVM tests pass. | 2026-05-25 Task 10: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL. | PASS | local terminal | Does not replace device QA. |
| QA-ENV-04 | Device APK build | Run `bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/` and `shasum -a 256 android/app/build/outputs/apk/debug/app-debug.apk`. | APK base URL points to current Mac LAN backend; sha256 recorded. | 2026-05-25 Task 10 PASS with base URL `http://192.168.0.118:8000/`; path `android/app/build/outputs/apk/debug/app-debug.apk`; size 16471142; sha256 `28fdd63f6cd6e9ef71c27d0dde2c8ce274d7980ea06d0a9e50e2d2248fa0ddaa`; BuildConfig base URL verified. | PASS | local terminal | No install attempted because no device connected. Rebuild after backend URL changes or app code changes. |

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

## 3A. Account and parent-operated login

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-AUTH-01 | Register one child account | Launch app with no saved token; create a synthetic child account from the parent-operated screen. | Registration succeeds, app enters child chat, and child UI never asks the child to manage credentials. |  | NOT_RUN |  | Do not record password/token. |
| QA-AUTH-02 | Login existing account | Log out, then log in with the same synthetic username/password. | Login succeeds and settings/report/conversation use that account child_id. |  | NOT_RUN |  |  |
| QA-AUTH-03 | Persistent session | Close/relaunch the app after login. | App remains logged in and opens the child experience without retyping password. |  | NOT_RUN |  |  |
| QA-AUTH-04 | Manual logout | From家长设置 tap logout. | Token clears and app returns to parent-operated login/register screen. |  | NOT_RUN |  |  |
| QA-AUTH-05 | Invalid credentials | Try an incorrect password for a synthetic account. | App shows a parent-facing failure message; child UI does not expose token/server internals. |  | NOT_RUN |  |  |
| QA-AUTH-06 | Invalid or expired token | Use a synthetic saved session after backend logout/expiry or force `/auth/me` 401 on app launch. | Saved token clears and app returns to parent-operated login/register screen; no token/debug credential is shown. |  | NOT_RUN |  | Backend and ViewModel unit tests cover this; device relaunch still required. |

## 4. Opening greeting

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-OPEN-01 | First screen opening | Start app with backend running after login. | Ready state appears quickly; one short personalized 小白狐 opening may arrive without blocking first screen or remote TTS. |  | NOT_RUN |  | Request id from opening call. |
| QA-OPEN-02 | Child speaks before late opening | Immediately start voice/text turn after entering chat. | Late opening does not insert above the child’s active turn. |  | NOT_RUN |  |  |
| QA-OPEN-03 | Nickname/display-name priority | Set fictional child nickname/display name in家长设置, restart chat. | Opening uses nickname first, display name second, and no forced real name when empty. |  | NOT_RUN |  | Do not use real child name. |
| QA-OPEN-04 | Interest callback safety | With synthetic low-sensitivity interest seed, open chat. | Opening may lightly revisit one topic and allows switching away; no pressure to continue. |  | NOT_RUN |  | Backend/log evidence only; no raw memory text. |
| QA-OPEN-05 | Slow opening trace | Trigger a slow synthetic opening/TTS path. | Evidence has backend `request_id`, `app.opening_timing` fields `model_ms`, `tts_ms`, `total_ms`, `audio_url_present`, `fallback_used`, plus Android video timestamp; no raw opening text or parent_message_raw. |  | NOT_RUN |  | Task 10 backend unit tests cover non-sensitive log shape and TTS timeout fallback. |

## 4A. Parent settings child profile

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-SETTINGS-01 | Child profile fields | In家长设置, enter fictional nickname, age, optional grade, call preference, interests, and topic boundaries. | Settings save successfully; child age/profile context affects later prompt metadata without exposing parent raw notes to child UI. |  | NOT_RUN |  | Do not use real child name or private family details. |
| QA-SETTINGS-02 | Visible schedule deemphasis | Open家长设置. | 放学后/作业/睡前 time ranges are not the main visible v0.1 setup burden; time remains gentle context only. |  | NOT_RUN |  | Existing backend schedule compatibility remains. |
| QA-SETTINGS-03 | Invalid age | Enter age outside 5-10. | UI asks for 5-10 or blank; no crash. |  | NOT_RUN |  |  |
| QA-SETTINGS-04 | Hidden schedule closeout | Save settings after backend already has a synthetic custom schedule. | Save succeeds even if hidden schedule UI defaults are not visible; existing schedule is preserved and hidden default times are not re-saved as a side effect. |  | NOT_RUN |  | Automated ViewModel test covers this; device still needs save/load QA. |

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
| QA-TTS-06 | Perceived latency breakdown | For one slow synthetic turn, record backend request_id and Android logcat around the turn. | Backend has model/TTS/stream timing; Android has `XiaobaohuTtsTiming` URL received/start/done/error lines with request_id or turn_id; evidence contains IDs and timings only. |  | NOT_RUN |  | Do not paste child text, full reply, raw audio, parent_message_raw, provider key, or complete signed audio URL. |

## 6A. TTS provider fallback and experimental local TTS

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-TTS-FB-01 | MiMo VoiceClone baseline | `CHILD_AI_TTS_PROVIDER=mimo`, `SHERPA_ONNX_TTS_ENABLED=false`, `TTS_ENABLE_LOCAL_FALLBACK=false`. Send a normal turn. | MiMo VoiceClone generates audio; `provider=mimo` in response and cache metadata. |  | NOT_RUN |  | Primary path. Record request_id. |
| QA-TTS-FB-02 | sherpa-onnx as primary | `CHILD_AI_TTS_PROVIDER=sherpa_onnx`. Send a normal turn. | sherpa-onnx generates audio locally; no API key needed; no network call to MiMo. |  | NOT_RUN |  | sherpa-onnx model files must exist locally. |
| QA-TTS-FB-03 | Local fallback off by default | `TTS_PROVIDER=mimo`, `SHERPA_ONNX_TTS_ENABLED=true`, `TTS_ENABLE_LOCAL_FALLBACK=false`. Force MiMo timeout. | MiMo error propagates; NO automatic fallback to sherpa-onnx; child sees gentle TTS failure. |  | NOT_RUN |  | Config gate: `TTS_ENABLE_LOCAL_FALLBACK` must be explicit. |
| QA-TTS-FB-04 | Local fallback on, transient error | `TTS_PROVIDER=mimo`, `SHERPA_ONNX_TTS_ENABLED=true`, `TTS_ENABLE_LOCAL_FALLBACK=true`. Force MiMo timeout. | Fallback to sherpa-onnx; audio plays; `provider=sherpa_onnx` in response; backend logs `tts_primary_failed_fallback`. |  | NOT_RUN |  | Record request_id and fallback log event. |
| QA-TTS-FB-05 | Config error NOT masked | `TTS_PROVIDER=mimo`, `SHERPA_ONNX_TTS_ENABLED=true`, `TTS_ENABLE_LOCAL_FALLBACK=true`. Remove sherpa model files, force MiMo config error. | Config error raises; does NOT silently fall back to sherpa-onnx. |  | NOT_RUN |  | TtsProviderConfigurationError always propagates. |
| QA-TTS-FB-06 | No system TTS mixing | Observe TTS playback across all fallback scenarios. | Android never plays system TextToSpeech; only backend-generated WAV from `/media/tts/...` is used. |  | NOT_RUN |  | System TTS is dev diagnostic only. |
| QA-TTS-FB-07 | Opening TTS latency | Measure opening greeting TTS from request to audio playback. | Opening TTS completes within `OPENING_TTS_SOFT_TIMEOUT_MS` (default 15s); cache hit should be near-instant. |  | NOT_RUN |  | Record backend `tts_call_finished` elapsed_ms. |

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
| QA-TOPIC-01 | Same topic low engagement | Use a synthetic game/CS or sports topic for 3+ turns, then give a short flat reply. | Model `conversation_control` or safe fallback recommends soft_shift; 小白狐 offers a gentle topic shift with curated/backend seeds instead of deeper interview. |  | NOT_RUN |  | Evidence should be request_id/video timestamp, not raw text. |
| QA-TOPIC-02 | Engaged same topic | Use a synthetic topic where the child gives longer engaged replies. | 小白狐 may continue naturally; topic shift should not fire too early. |  | NOT_RUN |  |  |
| QA-TOPIC-03 | Backend generated topic choices | Trigger a backend soft_shift or inspect returned `ui_actions`. | Small chips come from backend quick actions/control, may include safe interest/curated labels, and do not cover voice/TTS controls or look like tasks/rewards. |  | NOT_RUN |  | No Android hard-coded independent topic chips; no live web/trend fetch. |

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
| QA-PARENT-01 | Normal tap | Logged-in child chat: tap small “大人” entry. | Opens parent target choice or parent page according to current logged-in path; no token/debug details are shown. |  | NOT_RUN |  | Child account login replaces default PIN path. |
| QA-PARENT-02 | Parent report entry | Choose家长日报. | 家长日报 opens for the current logged-in child account. |  | NOT_RUN |  |  |
| QA-PARENT-03 | Parent settings entry | Choose家长设置. | 家长设置 opens for the current logged-in child account and can return to chat. |  | NOT_RUN |  |  |
| QA-PARENT-04 | Dev PIN fallback | If a dev build enables PIN fallback, try wrong/correct PIN. | PIN protects only the dev fallback path; default logged-in path does not depend on PIN. |  | NOT_RUN |  | Dev PIN is not production auth. |

## 11. Parent report

| ID | Scenario | Steps | Expected result | Actual result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| QA-REPORT-01 | Success | Generate report from synthetic structured memories. | Summary, “今晚可以怎么接一句”, “今日聊了什么”, and avoid-follow-up display; no raw chat transcript. |  | NOT_RUN |  |  |
| QA-REPORT-02 | model_failed/model_blocked | Force model failure or policy block. | Parent sees family-safe “小结还没准备好” style message, not provider/config details. |  | NOT_RUN |  |  |
| QA-REPORT-03 | Empty material | Generate report with no day material. | Empty state is calm and does not invent child activity. |  | NOT_RUN |  |  |
| QA-REPORT-04 | Tonight bridge | Inspect top bridge. | Bridge is a concrete real-life suggestion, not surveillance or a demand. |  | NOT_RUN |  |  |
| QA-REPORT-05 | Topic/content summary | Generate a report after synthetic game/image/learning turns. | Topic cards summarize content and intent without quoting child原文. |  | NOT_RUN |  |  |
| QA-REPORT-06 | Avoid follow-up | Inspect “今晚先不追问”. | It tells the parent what not to over-ask, including old topics or answer chasing when relevant. |  | NOT_RUN |  |  |
| QA-REPORT-07 | CS/game summary | Generate a report from a synthetic CS/game conversation with friends/team/map/loss/short replies. | Report summarizes topic/content at a high level, gives a concrete tonight bridge, includes avoid_followup, and does not show raw transcript/provider/debug/scoring wording. |  | NOT_RUN |  | Automated synthetic test covers backend summary; parent UI device reading still pending. |

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

## 16. Task 06 automated refinement snapshot

```text
Date: 2026-05-24
Scope: parent settings child profile simplification; conversation topic shift and curated seeds; parent report topic/content summary redesign; child UI polish thin slice.
Backend tests: `bash scripts/test_backend.sh` -> 424 passed; `bash scripts/lint_backend.sh` -> passed.
Android tests: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL.
Real-device QA: NOT_RUN; earlier doctor reported no attached physical Android device.
Device QA required: Redmi K60 / Honor Pad 5 for settings readability, topic shift naturalness, parent report hierarchy, and 小白狐 phase chip/layout.
```

## 17. Task 07 automated closeout snapshot

```text
Date: 2026-05-24
Scope: parent schedule closeout; reviewed age-aware topic seed pack; child-facing idle shift chips; TTS latency observability; CS/game parent report summary hardening.
Backend tests: `bash scripts/test_backend.sh` -> 428 passed; `bash scripts/lint_backend.sh` -> All checks passed.
Android tests: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL; `bash scripts/android_gradle.sh assembleDebug` -> BUILD SUCCESSFUL.
Real-device QA: NOT_RUN; doctor reported no attached physical Android device.
Device QA required: Redmi K60 / Honor Pad 5 for hidden schedule save/load, shift chip layout, TTS log collection, slow-turn diagnosis, and parent report CS/game readability.
```

## 18. Task 08 real-device QA round 2 package snapshot

```text
Date: 2026-05-24
Scope: Lane A only. No new Redmi K60 / Honor Pad 5 video, backend request_id, or Android XiaobaohuTtsTiming logcat evidence was available, so Lane B/C/D code fixes were skipped.
Source code commit before Lane A docs closeout: a0255d79647eaecd86013ed90a7063f259e10dcf
Backend tests: `cd backend && /opt/homebrew/bin/conda run --no-capture-output -n child-ai python -m pytest` -> 428 passed.
Backend lint: `cd backend && /opt/homebrew/bin/conda run --no-capture-output -n child-ai python -m ruff check .` -> All checks passed.
Android tests: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL.
Android build: `bash scripts/android_gradle.sh assembleDebug` -> BUILD SUCCESSFUL.
Device APK build: `bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/` -> PASS.
APK path: android/app/build/outputs/apk/debug/app-debug.apk
APK base URL: http://192.168.0.118:8000/
APK size: 16471142 bytes
APK sha256: 811a87abd220e1c102619e827beedb505f0771658b533871e44af02a134d0c86
Device connection: adb available; no connected physical Android device.
Slow-turn latency classification: NOT_RUN because no matching request_id + XiaobaohuTtsTiming logcat + video/timestamp evidence exists.
P0 issues: none observed in this run.
P1 issues: none observed in this run.
P2 issues: none observed in this run; device layout/audio/report naturalness still unvalidated.
P3 issues: git reported loose-object gc housekeeping warnings; not product/runtime blocking.
Remaining NOT_RUN QA: all Redmi K60 / Honor Pad 5 device rows in sections 3-14, especially QA-TTS-06, QA-TOPIC-03, QA-SETTINGS-04, QA-REPORT-07, QA-DEVICE-RK60-01/02, and QA-DEVICE-HP5-01/02.
```

## 19. Task 09 account and personalization snapshot

```text
Date: 2026-05-25
Scope: Child account/auth foundation; 父亲->家长 copy; model-driven conversation_control; personalized opening v2; backend-generated interest-aware topic choices.
Backend tests: `bash scripts/test_backend.sh` -> 441 passed.
Backend lint: `bash scripts/lint_backend.sh` -> All checks passed.
Android tests: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL.
Real-device QA: NOT_RUN; no Redmi K60 / Honor Pad 5 device evidence was available in this implementation run.
Device QA required: Redmi K60 / Honor Pad 5 for register/login/persistent session/logout, 家长设置/日报 default logged-in entry, opening v2 non-blocking behavior, CS/game conversation_control naturalness, backend topic choices layout, and auth screens on low-end landscape.
Data boundary: do not record passwords, bearer tokens, real child names, raw transcript, raw audio, raw image, provider key, parent_message_raw, or DB dumps.
```

## 20. Task 10 Task09 closeout and QA package snapshot

```text
Date: 2026-05-25
Scope: Auth/account closeout; opening v2 latency closeout; model control/topic choice trace hardening; QA package and docs closeout.
Backend tests: `bash scripts/test_backend.sh` -> 453 passed.
Backend lint: `bash scripts/lint_backend.sh` -> All checks passed.
Android tests: `bash scripts/android_gradle.sh test` -> BUILD SUCCESSFUL.
Android build: `bash scripts/android_gradle.sh assembleDebug` -> BUILD SUCCESSFUL.
Model trace runner: `conda run -n child-ai python scripts/run_model_trace_scenarios.py --output /tmp/task10_model_trace_review.md` -> MODEL_TRACE_SCENARIOS: PASS, scenarios=26, traces=26.
Device APK build: `bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/` -> PASS.
APK path: android/app/build/outputs/apk/debug/app-debug.apk
APK base URL: http://192.168.0.118:8000/
APK size: 16471142 bytes
APK sha256: 28fdd63f6cd6e9ef71c27d0dde2c8ce274d7980ea06d0a9e50e2d2248fa0ddaa
Device connection: adb available; no connected physical Android device.
Real-device QA: NOT_RUN; no Redmi K60 / Honor Pad 5 install, video, request_id, opening timing, or XiaobaohuTtsTiming evidence was collected in this run.
Remaining NOT_RUN QA: all Redmi K60 / Honor Pad 5 device rows in sections 3-14, especially QA-AUTH-01..06, QA-OPEN-01..05, QA-TOPIC-01..03, QA-TTS-06, QA-ANDROID-03, QA-DEVICE-RK60-01/02, and QA-DEVICE-HP5-01/02.
Data boundary: SharedPreferences token is a family-beta thin slice only, not production security hardening; do not record passwords, bearer tokens, real child names, raw transcript, raw audio, raw image, provider key, parent_message_raw, or DB dumps.
```

## Closeout rules

```text
1. Automated test PASS does not equal Redmi K60 / Honor Pad 5 PASS.
2. Mark real-device scenarios `NOT_RUN` until run on the named device.
3. Mark external provider scenarios `BLOCKED` when required env/policy/key is absent; do not call them done.
4. Evidence must be request_id/log path/video timestamp, not raw child text or raw media.
5. Any child-facing adult/debug wording, system TTS mixed voice, direct homework answer, secrecy language, or raw data leakage is a FAIL.
```
