# Backend

FastAPI backend for the v0.1 child AI growth agent MVP.

The current backend is local-first and test-stage real-path focused:

- Current QA must run the actual provider path for any feature that has entered
  the active test scope; mock/fake providers are only automatic-test doubles or
  exception fallbacks.
- Does not put provider keys or direct model/OCR/vision calls in Android.
- Keeps all child-facing AI decisions behind backend services such as `SafetyEngine`, `IntentClassifier`, `SceneOrchestrator`, `PromptManager`, and `ModelRegistry`.
- Routes child-facing replies through `ChildAgentRuntime`: `SceneOrchestrator`
  decides the scene strategy and safe fallback reply, `PromptManager` composes
  the prompt, `ModelRegistry` generates the child chat response, and
  `SafetyEngine.classify_output()` checks the output before return.
- Task 09 adds a local family-beta auth thin slice: a parent-operated child
  account maps to one child app space, Android sends a bearer token after
  login, and conversation/settings/report APIs use the authenticated child_id
  when present while explicit dev child_id remains supported for tests.
  Task 10 closes out the default logged-in route coverage for conversation,
  stream, opening, parent policy, parent report, and attachment JSON/multipart
  uploads. This is still a family-beta thin slice, not production auth.
- Retrieves non-safety structured memory before `ChildAgentRuntime`, and writes
  rule-based conversation memory after routing. Memory evidence uses summary
  sources only; raw chat, full transcripts, raw audio, and raw photos are not
  stored as long-term evidence.
- E1 relationship memory is rule-first and local: low-sensitivity
  `interest_seed`, `topic_boundary`, and `proud_moment` summaries can be
  created from child conversation turns, while operation asides, bystander
  prompts, privacy details, high-risk safety content, and raw/full transcripts
  are filtered out before storage. The E1.1 hardening keeps memory writes
  best-effort, dedupes active interest seeds by child/topic across sessions,
  and only lets opening lightly revisit the latest low-sensitivity seed.
- Treats child chat as open-ended conversation. Time periods and scenes provide
  context, safety boundaries, and fallback replies; they should not force every
  ordinary message into a fixed script.
- Current direction is freedom-first: `conversation.open` is the default base.
  Time context, parent free-form guidance, memory, recent turns, and images are
  prompt/context inputs; safety, privacy, explicit learning help, explicit
  bedtime closeout, and confirmed parent hard rules are guardrails.
- Attachment now supports the active real image path for “拍给小白狐看”:
  Android uploads a real system-camera or system-picker image to
  `POST /api/v1/attachments/images`, the backend runs MiMo vision for the image
  summary, and conversation receives only controlled `image_context` through
  `attachment_id`. The older JSON/mock attachment path remains for automated
  tests and explicit fallback diagnostics, not the child-facing default.
- Uses `ConversationHistoryService` for short-term, in-memory recent turns so
  ordinary chat can keep context within one running backend process. This is not
  a durable chat database; service restart clears it, and full chat transcripts
  are not written to long-term memory or parent reports.
- Normalizes child-facing model replies for voice-first use: short natural
  sentences, no Markdown/list formatting, and usually one main question.
- Returns child-facing reply metadata for future voice and 小白狐 animation
  work: `voice_enabled`, optional `audio_url`, `emotion`, and `agent_motion`.
- Speech recognition v1 is backend local-first ASR: Android records only after
  an explicit tap and uploads short audio to the backend ASR endpoint. The
  preferred real provider is sherpa-onnx + SenseVoice-Small int8; if local ASR
  raises an error, the service can fall back to the configured original ASR
  provider. Child mode auto-sends a non-empty transcript to conversation; the
  pending transcript panel remains only for DevSettings / parent debugging.
  Raw child audio is never stored long-term; cloud MiMo ASR fallback remains
  controlled by parent authorization and ASR policy flags.
- Opening greeting is available at `POST /api/v1/conversation/opening`.
  Task 09 upgrades it to personalized opening v2: it uses time context, account
  profile, parent guidance, topic boundaries, recent low-sensitivity memory,
  and a model-generated short greeting when safe/available, with deterministic
  fallback on provider failure. Task 10 adds non-sensitive `app.opening_timing`
  logs and a short TTS soft timeout so slow/failed opening audio does not block
  the text opening. Android should treat opening/TTS as non-blocking and keep
  the first screen Ready.
- Parent policy supports `child_nickname` and `child_display_name`; Android
  parent settings can edit them, and opening greeting uses nickname first,
  display name second, then no forced call name.
- Task 06 refines parent policy for family beta: Android parent settings now
  emphasize child age, optional grade, call preference, interests, and topic
  boundaries through `communication_preferences`. Visible schedule editing is
  de-emphasized for v0.1; time periods remain gentle context, not hard scene
  locks.
- Open conversation now exposes `conversation_control` from the same child_chat
  model call. The model can signal high/medium/low engagement, continue,
  soft_shift, stop, and suggested next moves; program guardrails still override
  safety, privacy, bedtime, explicit boundaries, fallback, and metrics. Task 10
  records non-content `conversation_control_trace` summaries for synthetic trace
  review without raw child text.
- Topic suggestions are generated by backend quick actions from child profile
  interests, topic boundaries, age-aware curated seeds, recent topic, and
  conversation_control. Task 10 keeps model/profile choices ahead of old keyword
  fallbacks and filters boundary synonyms such as CS/game or running/sports.
  Android should render backend actions and not provide hard-coded independent
  topic chips.
- Parent report v2 now includes topic overview, conversation summary, tonight
  bridge, and avoid-follow-up fields while keeping model-first generation and
  no raw transcript output.
- 小白狐 voice output now has a backend TTS path: `POST /api/v1/tts/xiaobaohu`
  can generate or return a cached wav URL. For QA, enable the intended real TTS
  provider or mark the missing external condition as BLOCKED/FAIL. Android now
  prefers `reply.audio_url` playback; system TextToSpeech is not used as the
  child-facing automatic fallback when remote audio fails.
- Task 04 adds Healthy Engagement observability through
  `app.healthy_engagement` logs. These records contain counts, boundary
  signals, age band, scene, latency, request_id, and hashed IDs only; they must
  not contain full child text, full assistant text, raw audio, raw images,
  parent_message_raw, provider keys, or full provider bodies.
- Task 08 Lane A prepared the next real-device QA package only. No new Redmi
  K60 / Honor Pad 5 video, backend request_id, or Android
  `XiaobaohuTtsTiming` logcat evidence was available in that run, so no
  evidence-based Lane B/C/D fixes were made.

If Android replies look like fixed templates such as “听起来可以聊”, the backend
is probably not running the intended real chat provider for the current QA
target. Restart with the temporary environment variables in the Mimo section
below when needed; do not put the real API key into git, Android, docs, tests,
or screenshots.

## Task 09/10 Auth And Personalization Thin Slice

Task 09/10 is a family-beta foundation, not production auth compliance:

- `child_accounts`: stores account id, username, password hash, basic child
  profile fields, `created_by_guardian`, timestamps, and last login.
- `auth_sessions`: stores server-side token hash, account id, creation,
  expiration, and optional revocation time. Raw bearer tokens are returned only
  once to the client and are not stored plaintext server-side.
- Password hashing uses PBKDF2-SHA256 with per-password salt; no plaintext
  password is stored in DB or tests.
- `POST /api/v1/auth/register` creates one parent-operated child account,
  initializes/updates the matching parent policy, and returns a bearer token.
- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, and
  `POST /api/v1/auth/logout` manage the local session. Sessions are intended to
  persist on Android until manual logout or expiry/revocation.
- Existing conversation, opening, stream, parent policy, parent report, and
  attachment upload APIs accept the bearer token and prefer the authenticated
  child_id; explicit child_id remains available for local dev/test compatibility.
- Expired or revoked sessions return 401 on authenticated routes. Android clears
  a saved family-beta session after `/auth/me` fails and returns to the
  parent-operated login/register screen.
- Android persists the bearer token in SharedPreferences only for the family-beta
  thin slice. Do not describe this as production security hardening.

Product copy now uses “家长” by default. Code and API names such as `Parent*`
remain for compatibility until a separate refactor is approved.

## Task 10 Device QA Evidence

Latest Task 10 QA APK package:

```text
path=android/app/build/outputs/apk/debug/app-debug.apk
base_url=http://192.168.0.118:8000/
size_bytes=16471142
sha256=28fdd63f6cd6e9ef71c27d0dde2c8ce274d7980ea06d0a9e50e2d2248fa0ddaa
build_time_utc=2026-05-25T04:10:50Z
real_device_qa=NOT_RUN
```

For one slow synthetic opening or TTS turn, collect backend timing and Android
playback timing for the same request:

```bash
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
adb logcat -v time | grep XiaobaohuTtsTiming
```

Use the backend `request_id` to align these logs:

- `conversation_turn_latency`: non-stream `model_ms`, `tts_ms`,
  `audio_url_present`, `turn_total_ms`.
- `conversation_opening_finished`: opening `model_ms`, `tts_ms`, `total_ms`,
  `audio_url_present`, `fallback_used`, `cache_hit`, `request_id`, and hashed
  child/session ids.
- `conversation_stream_finished`: stream `first_text_ms`, `tts_started_ms`,
  `first_audio_ms`, `turn_total_ms`.
- Android `XiaobaohuTtsTiming`: `remote_audio_url_received`,
  `remote_audio_playback_started`, `remote_audio_playback_done`, or
  `remote_audio_error`, with request/turn id and elapsed milliseconds.

Evidence must stay non-sensitive: request_id, timing fields, log paths, and
video timestamps are acceptable. Do not paste child text, full assistant text,
raw audio, raw photos, parent_message_raw, provider keys, DB dumps, or full
signed media URLs.

## Current Voice And Presentation Contract

The backend remains the decision and safety boundary. Android records explicit
tap-to-talk audio for backend ASR and uses remote 小白狐 audio for voice output;
child-facing content still flows through:

```text
SafetyEngine -> IntentClassifier -> SceneOrchestrator -> PromptManager -> ModelRegistry -> output safety check
```

Current backend contract:

- Accept child text through `POST /api/v1/conversation/message` and NDJSON
  stream text through `POST /api/v1/conversation/stream`.
- Treat v1 speech input as voice-first in child mode: ASR ok with non-empty
  transcript is sent automatically by Android. Confirm-before-send remains a
  debug/father mode only; hands-free conversational mode is still a future
  product phase and should not change the v1 backend contract.
- ASR v1 target is backend local-first ASR using sherpa-onnx +
  SenseVoice-Small int8, with MiMo audio input / ASR retained as an optional
  fallback. Android must not call MiMo directly or store provider API keys.
- Raw audio uploaded for ASR must be short-lived request data only: no database
  persistence, no logs, no memory, no test fixtures with real child recordings.
- External audio and child text transmission must pass the confirmed product
  decision and provider gate review. Once a feature is in active QA, configure
  that approved provider path explicitly instead of treating an unconfigured
  runtime as a completed test. Local ASR does not require the external-audio
  policy flags but still must not persist raw audio.
- Return `reply.voice_enabled`, optional `reply.audio_url`, `reply.emotion`, and
  `reply.agent_motion` for Android TTS and 小白狐 presentation.
- Use `POST /api/v1/tts/xiaobaohu` for backend-generated 小白狐 speech audio.
- Use `POST /api/v1/attachments/images` for real image upload from Android.
  Conversation follow-up sends the returned `attachment_id`; do not send image
  base64 in conversation payloads or logs.
- Use `POST /api/v1/conversation/opening` when the child chat screen first
  becomes visible. Call-name priority is `child_nickname`,
  `child_display_name`, then no forced call name. Opening should not block on
  cold TTS generation.
- Never use voice or presentation metadata to weaken learning-answer, secrecy,
  trusted-adult, or long-term raw-data storage safety rules.

## Setup

Project convention uses the local conda environment from `docs/session_process/README.md`:

```bash
eval "$(/opt/homebrew/bin/conda shell.zsh hook)"
conda activate child-ai
cd backend
python -m pip install -e ".[dev]"
```

If the environment is not activated, root scripts will try `/opt/homebrew/bin/conda run --no-capture-output -n child-ai python` before falling back to system Python. You can override this explicitly:

```bash
PYTHON_BIN="/opt/homebrew/bin/conda run --no-capture-output -n child-ai python" bash scripts/test_backend.sh
PYTHON_BIN=python3 bash scripts/lint_backend.sh
```

For local environment diagnosis:

```bash
bash scripts/doctor_local_env.sh
```

## Run

From the repository root:

```bash
bash scripts/dev_backend.sh
```

Or from `backend/` after activating the environment:

```bash
python -m uvicorn app.main:app --reload
```

For Android device or tablet LAN testing, listen on all interfaces:

```bash
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

Then use the Mac mini LAN address from the Android build, for example:

```bash
bash scripts/android_gradle.sh assembleDebug -PconversationApiBaseUrl=http://MAC_MINI_LAN_IP:8000/
```

Default local API docs:

- `GET http://127.0.0.1:8000/docs`
- `GET http://127.0.0.1:8000/api/v1/health`

## Test And Lint

From the repository root:

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
```

From `backend/`:

```bash
python -m pytest
python -m ruff check .
```

Q1 scenario tests live in:

```text
app/tests/test_scenarios_v0_1.py
```

They cover:

- after-school check-in
- learning help
- direct-answer request handling
- child does not want to talk
- watch-level peer trouble routing to `safety.gentle_checkin`
- low privacy boundary routing to `privacy.boundary`
- high-risk safety guardian routing with parent attention
- bedtime reflection
- parent goal influencing reply wording
- model fallback
- automatic conversation memory hooks in
  `app/tests/test_conversation_memory_hooks.py`, including learning patterns,
  low-energy emotion observations, high-risk safety memory, watch observations,
  privacy-boundary summaries, relationship interest seeds, topic boundaries,
  proud moments, parent report visibility, and safety-memory retrieval
  isolation

## Demo Scenarios

Run a local demo from the repository root:

```bash
bash scripts/demo_backend_scenarios.sh
```

By default the script starts a temporary backend server on `127.0.0.1:18080`, runs safe mock scenarios, prints the active scene, intent, risk level, quick actions, and reply, then stops the server.

To point the demo at an already running server:

```bash
DEMO_BASE_URL=http://127.0.0.1:8000 bash scripts/demo_backend_scenarios.sh
```

The demo uses only fictional IDs such as `child_demo_001` and mock homework text. It does not use real child data, real photos, real OCR, or real model calls.

## Local E2E API Check

With a backend server already running, validate the Android-facing API contract:

```bash
bash scripts/e2e_local_api_check.sh
```

To target a LAN server:

```bash
E2E_BASE_URL=http://MAC_MINI_LAN_IP:8000 bash scripts/e2e_local_api_check.sh
```

The check covers health, after-school, learning help, mock homework attachment, bedtime, high-risk safety, parent policy update, and parent report read. It uses fictional IDs and mock homework text only.

With automatic memory enabled, the parent report step may include structured
conversation summaries generated during the same process. It still does not
return evidence fields, quote summaries, or full chat transcripts.

## Family Test Smoke

Family-test smoke scripts live under `scripts/` and are designed to catch
configuration drift before handing an APK to device QA.

The current family-beta device runbook is:

```text
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Use it to separate automated smoke results from Redmi K60 / Honor Pad 5 real
device QA. Evidence should be request_id, log path, APK hash, or video
timestamp, not raw child content or raw media.

```bash
bash scripts/setup_local_postgres.sh
bash scripts/smoke_backend_local.sh
bash scripts/smoke_voice_stack.sh
bash scripts/smoke_db_persistence.sh
bash scripts/check_asr_real_status.sh
python scripts/check_local_sensevoice_asr_status.py --fallback mock
bash scripts/smoke_vision_model_opt_in.sh
```

Coverage:

- `smoke_backend_local.sh` starts a temporary mock backend by default and checks
  `/api/v1/health/detail`, `/conversation/message`, `/conversation/stream`,
  parent policy save/read, and parent report read.
- `smoke_voice_stack.sh` starts a temporary mock backend and checks mock ASR,
  mock TTS, and stream `include_tts=true` through `audio_ready`.
- `smoke_db_persistence.sh` requires local PostgreSQL and migrations. If the
  database is unavailable, it prints a clear `SKIP` with
  `bash scripts/setup_local_postgres.sh` and must not be counted as pass.
- `setup_local_postgres.sh` first tries Docker Compose, waits for the local
  PostgreSQL healthcheck, runs migrations, then runs DB persistence smoke. If
  Docker is unavailable on macOS, it tries Homebrew `postgresql@16` and creates
  the `child_ai` role and `child_ai_dev` database idempotently. If Docker,
  Homebrew, or permissions are unavailable, it reports `POSTGRES_SETUP: BLOCKED`
  with a concrete reason.
- `check_asr_real_status.sh` sources `.env`, applies a temporary MiMo ASR
  smoke overlay, starts a temporary backend, and generates a synthetic
  non-child fake WAV when no safe smoke audio path was provided. This validates
  the cloud fallback provider request chain without permanently changing
  `.env`.
- `check_local_sensevoice_asr_status.py` validates the local SenseVoice primary
  path with non-child WAV input, checks `numpy` / `sherpa_onnx` and model files,
  and writes `docs/LOCAL_ASR_SENSEVOICE_SMOKE_V0_1.md`. If no audio is given it
  generates a 1s silent WAV for provider/init verification only; a successful
  recognition smoke should pass an explicit non-child WAV with `--expect-pass`.
- `smoke_vision_model_opt_in.sh` verifies the OpenAI-compatible MiMo vision path
  by sourcing `.env`, applying a temporary MiMo image smoke overlay, starting a
  temporary backend, and generating a fake/test PNG when no safe image path was
  provided. It never prints image base64, the full image description, API keys,
  or provider raw response.

MiMo ASR fallback smoke:

```bash
bash scripts/check_asr_real_status.sh
```

The ASR smoke must not print API keys, audio base64, transcript text, or
provider raw response, and it must not be run with real child recordings during
development smoke.

MiMo vision/OCR smoke:

```bash
bash scripts/smoke_vision_model_opt_in.sh
```

The legacy vision smoke path can post a safe data URI to
`/api/v1/conversation/attachment` for provider-contract testing. The active
Android QA path posts multipart image bytes to `/api/v1/attachments/images` and
must not be reported as PASS unless MiMo vision actually handled the image.
Normal text chat uses `CHILD_AI_MIMO_MODEL=mimo-v2.5-pro`; image/vision/OCR
uses `CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5` because MiMo image understanding is
served by the native multimodal model, not the pro text model. The MiMo provider
uses `max_completion_tokens` for MiMo chat completions.

Real-path development backend:

```bash
CHILD_AI_MIMO_API_KEY=... bash scripts/run_real_path_dev_backend.sh
```

This script applies a temporary process env overlay for active QA:

```text
child_chat -> mimo_child_chat / mimo-v2.5-pro
vision/OCR -> mimo_vision / mimo-v2.5
ASR -> local_sensevoice first, MiMo fallback
TTS -> MiMo VoiceClone first
model debug trace -> default system component for local prompt review
```

Do not commit `.env`, real keys, uploaded images, model files, DB dumps, or
base64 image/audio payloads.

## Local PostgreSQL Persistence

The v0.1-dev persistence target is local PostgreSQL for family testing. DB1-A
adds the database foundation. DB1-B2/B3/B4/B5 now cover the local persistence
thin slice:
`ParentPolicyService` reads/writes `parent_policies` through a SQLAlchemy
repository when PostgreSQL is available, including `parent_message_raw`,
`parent_message_updated_at`, `child_nickname`, and `child_display_name`.
DB1-B3 records ordinary `/api/v1/conversation/message` turns and
completed `/api/v1/conversation/stream` turns with a best-effort repository. It
upserts `conversation_sessions`, stores the child message, stores one final
agent message, and stores a non-sensitive routing decision summary. Stream turns
are recorded once after completion; text deltas, full stream event lists, and
per-segment TTS text are not stored. If the local database is unavailable in
dev/test, persistence failures are logged with hashed identifiers and the
conversation response or stream output is not blocked.

DB1-B4 records structured `MemoryService` items in `memory_items` when
PostgreSQL is available. The service keeps the same validation boundary as the
in-memory repository: memory content must be structured summary material,
evidence must be short `quote_summary` style evidence, safety memories remain
parent-visible, and forbidden raw evidence sources are rejected before storage.
Relationship memory E1 uses the same table and schema: `interest_seed`,
`topic_boundary`, and `proud_moment` are stored as low-sensitivity structured
summaries with metadata, not as child verbatim text.
If PostgreSQL is unavailable, MemoryService falls back to the process-local
repository without blocking conversation or Android QA.

DB1-B5 records generated `ParentReportService` reports in `parent_reports`.
`get_daily_report()` first reads an existing model-generated report for
`child_id + date`; if none exists or same-day materials changed, it builds a
minimal evidence packet from same-day conversation messages, routing/scene/risk
signals, and parent-visible structured memory, then calls
`ModelTaskType.PARENT_REPORT`. Only valid structured model output is saved as a
formal report. Provider failure, policy blocking, empty output, or invalid JSON
returns `generation_status=model_failed|model_blocked` with a retry message
instead of showing a deterministic rule report as success. Repository failure
does not leak report content; logs contain only hashed identifiers, date,
operation, and error type.
Parent reports can use relationship memories as model evidence for low-pressure
real-world conversation starters with an avoid note, for example gently asking
about a running competition without interrogating distance or body symptoms.

Local dev database:

```bash
bash scripts/setup_local_postgres.sh
```

Manual Docker-only equivalent:

```bash
docker compose -f docker-compose.local.yml up -d postgres
bash scripts/db_migrate.sh
bash scripts/smoke_db_persistence.sh
```

`smoke_db_persistence.sh` is a local DB persistence smoke, not a provider
quality test. It uses synthetic data and a local smoke parent-report registry so
PostgreSQL checks do not depend on external model availability.

To reset the local schema during development:

```bash
bash scripts/db_reset_local.sh --yes
```

Default local database URL:

```text
CHILD_AI_DATABASE_URL=postgresql+psycopg://child_ai:child_ai@localhost:5432/child_ai_dev
```

Initial tables:

```text
children
parent_policies
conversation_sessions
conversation_messages
routing_decisions
memory_items
parent_reports
model_debug_traces
tts_cache_records
```

After pulling DB1 changes, run migrations:

```bash
bash scripts/db_migrate.sh
```

Data boundary:

- This is local family-use storage, not a cloud multi-tenant production design.
- Ordinary `/api/v1/conversation/message` and completed
  `/api/v1/conversation/stream` final text may be stored locally for context,
  review, and future parent report material.
- Stream persistence stores one turn only. It may store the first audio segment
  URL and non-sensitive counts such as `audio_segment_count`, `has_audio`, and
  `tts_error_count`; it must not store every `text_delta` or the full stream
  event list.
- Raw audio files, raw photos, API keys, model keys, and debug internals must
  not be written to PostgreSQL.
- Prompt text, `parent_message_raw`, provider raw responses, audio base64, and
  raw image/OCR debug data must not be written to conversation persistence.
- `memory_items` stores structured summaries, tags, short evidence summaries,
  sensitivity, visibility flags, parent-attention flags, expiry, and optional
  embedding ids. It must not store raw media, full chat transcripts, prompts,
  debug internals, provider raw responses, or API keys.
- `parent_reports` stores parent-facing daily summary text, observations,
  structured safety alerts, suggested parent actions, generation status, and a
  same-day material fingerprint. It must not store memory evidence, quote
  summaries, raw chat transcripts, prompts, debug internals, provider raw
  responses, or API keys. ParentReport v2 is model-first: formal report content
  comes from `ModelTaskType.PARENT_REPORT`; deterministic/rule material is only
  an internal fallback/hints path and is not shown as a successful report when
  the model fails.
- `tts_cache_records` stores hashes and cache metadata, not full sensitive TTS
  input text.
- `model_debug_traces` is a required local testing component for prompt
  analysis. It stores model request/response traces by default in the current
  test phase, while still filtering API keys, Authorization headers, `.env`
  contents, raw media, base64 image/audio payloads, and provider raw HTTP
  headers.
- Parent free-text notes are stored in `parent_policies.parent_message_raw` for
  local family testing. They are prompt background only and must not be exposed
  in child-facing debug/UI.
- Any future cloud deployment or app-store release requires a separate child
  data compliance review before enabling remote persistence.

## Local Model Debug Traces

`DEV-TRACE-1` adds a local `model_debug_traces` table for product and prompt
analysis during family testing. It records calls made through
`ModelRegistry.generate()`, including request messages, `input_text`, context,
metadata, selected profile/provider/model, response text, structured output,
fallback/policy flags, error type, elapsed time, request id, and child/session
ids plus hashes.

Trace recording is enabled by default whenever the backend is running. Optional
settings only control trace detail:

```bash
export CHILD_AI_MODEL_DEBUG_TRACE_FULL_TEXT=true
export CHILD_AI_MODEL_DEBUG_TRACE_MAX_TEXT_CHARS=20000
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

Trace sanitization redacts secret-like fields and replaces raw image/audio data
URIs or long base64 payloads with `[raw_media_omitted]`. Trace write failures
are logged as warnings and never block model replies.

Inspect recent traces:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/show_model_debug_traces.py --limit 20
```

Clear traces:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/clear_model_debug_traces.py
```

Run the repeatable synthetic prompt review:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/run_model_trace_scenarios.py
```

The scenario runner uses synthetic providers for its own process, clears prior
trace rows, runs opening / child_chat / parent_report synthetic cases, verifies
that child_chat and parent_report model traces are recorded, and writes
`docs/MODEL_TRACE_SCENARIO_REVIEW_V0_1.md`. Task 09 opening v2 is
model-generated when safe/available and keeps deterministic fallback for
provider failure; ParentReport is model-first and should produce a
`parent_report` trace. The report is useful for prompt contract review, but it
is not real MiMo output, real child QA, or Android device validation.

Run the explicit real MiMo synthetic text-only review:

```bash
CHILD_AI_MIMO_API_KEY=... \
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/run_model_trace_scenarios.py \
    --provider mimo \
    --output docs/MODEL_TRACE_REAL_PROVIDER_REVIEW_V0_1.md
```

Real-provider mode is opt-in only. It applies a process-local MiMo overlay for
child_chat and parent_report, never writes `.env`, and does not use real child
audio/images, Android, CameraX, ASR, TTS, or vision. If the MiMo key is missing the runner
exits with `REAL_PROVIDER_BLOCKED` and does not report a mock pass as real
provider evidence. The Task 05 closeout run on 2026-05-24 reached
`REAL_PROVIDER_SMOKE: REVIEW_NEEDED` for 19 synthetic scenarios / 14 traces:
child_chat traces used provider/model `mimo/mimo-v2.5-pro` without fallback, the
deterministic self-harm trusted-adult fallback remained active, one parent_report
scenario timed out and fell back to mock, and one creative-share checker flagged
P2 review. The report for that run was written to `/tmp` and was not committed,
because it may contain synthetic provider outputs. Opening remains deterministic
by default. ParentReport was revised in PD-052 to model-first, so parent_report
traces are again required for model report QA; model failure is reported as
failed/blocked rather than replaced with a successful rule report.

Task 05 release-candidate smoke commands observed on 2026-05-24:

```bash
cd backend && conda run -n child-ai pytest
cd backend && conda run -n child-ai ruff check .
bash scripts/smoke_db_persistence.sh
conda run -n child-ai python scripts/run_model_trace_scenarios.py \
  --output /tmp/task05_model_trace_mock.md
conda run -n child-ai python scripts/run_model_trace_scenarios.py \
  --provider mimo \
  --output /tmp/task05_model_trace_real_provider.md
```

Observed results: backend pytest 417 passed, ruff passed, DB persistence smoke
passed with synthetic data, mock trace passed with 21 scenarios / 14 traces, and
real-provider synthetic trace returned `REVIEW_NEEDED` because parent_report
still needs review. None of these commands is real child QA or Android device
QA.

This table is not a production child-data strategy. Before any cloud deployment
or app-store release, prompt/response tracing must be redesigned and reviewed
under a separate child data compliance process.

## Freedom-first Conversation Notes

The default child conversation mode is `conversation.open`. Time context,
parent notes, memory, and image context are prompt context, not hard modes.
Safety, privacy, explicit homework help, and explicit bedtime closeout remain
guardrails.

Second-round routing fixes:

- Standalone “不会” or generic “题/问题” no longer triggers homework help.
- “我不会画这个小怪兽”, “游戏里有一道谜题”, and “我想出一个问题考你” stay in
  open conversation.
- Explicit homework phrases such as “我有一道题不会”, “这道题怎么做”, “帮我看看作业”,
  “数学题不会”, “练习册” enter `learning.homework_help`.
- Generic image sharing can continue into conversation through attachment
  context. The prompt receives the image summary and child caption, but no raw
  photo.
- Parent reports are generated when the parent opens the report screen. The
  service combines structured memory with same-day persisted conversation
  message/routing summaries, refreshes stale same-day reports when new chat
  material exists, and still avoids raw transcripts, evidence quotes, prompts,
  debug internals, provider raw responses, and raw media.

## Optional Xiaomi Mimo Provider

Xiaomi Mimo OpenAI-compatible provider support is available for controlled local testing and active QA. Use temporary backend environment variables, never Android-side keys or committed files.

Use environment variables only; never commit real API keys:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
export CHILD_AI_MIMO_MODEL=mimo-v2.5-pro
export CHILD_AI_MIMO_API_KEY="..."
```

For child-facing traffic, real external transmission must be backed by the active safety/data-retention review and explicit local configuration:

```bash
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=false
export CHILD_AI_MIMO_ALLOW_IMAGE=false
export CHILD_AI_MIMO_ALLOW_AUDIO=false
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=false
```

For a local developer-only Mimo smoke test, use temporary shell environment
variables or an ignored local root `.env`. Never write the real key to
committed files, docs, tests, Android, screenshots, or git:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_API_KEY="<temporary key>"
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=true
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
export CHILD_AI_MIMO_MAX_TOKENS=800
export CHILD_AI_MIMO_TIMEOUT_MS=30000
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

ParentReport v2 is model-first and uses the same MiMo text model by default, but
it needs a larger completion budget than short child chat. The backend defaults
`mimo_parent_report` to `CHILD_AI_PARENT_REPORT_MAX_TOKENS=4000` and
`CHILD_AI_PARENT_REPORT_TIMEOUT_MS=45000`; these can be overridden in local
shell env without changing child chat routing or vision/OCR routing.

`scripts/dev_backend.sh` loads the root `.env` when it exists, then starts
uvicorn. This is only for local development; `.env` must stay ignored and must
not be shared.

Only use fictional child IDs and test text in this mode. Keep
`CHILD_AI_MIMO_ALLOW_IMAGE=false` and `CHILD_AI_MIMO_ALLOW_AUDIO=false` unless a
separate review explicitly allows those data types.

`ModelRegistry.generate()` enforces this as a code-level gate before any
OpenAI-compatible provider call. When request metadata marks
`contains_child_data=true`, an external profile must have both
`allow_child_data=true` and `retention_policy_checked=true`; otherwise it uses
the configured safe fallback without calling the external provider. Metadata
`contains_image=true` and `contains_audio=true` also require `allow_image=true`
and `allow_audio=true`. Local test doubles are not blocked by this external
transmission gate, but they are not real provider evidence.

The child-facing runtime always marks child chat model requests with
`contains_child_data=true`. If prompt composition fails, the model registry
blocks or falls back from an external provider, the model call fails, the model
returns empty text, output safety is `high`/`critical`, or a learning-scene
model output appears to give a direct final answer, the runtime returns the
existing `SceneRouteDecision.reply_text` fallback instead of model text. This
preserves a deterministic safe reply for each routed scene without treating the
fallback as real provider success.

Output safety also blocks model replies that create secret relationships,
isolate the child from trusted adults, or imply the AI is the child's only or
best friend. These checks run after model generation and before the response is
returned to Android.

The Android app never stores model API keys. All model configuration belongs on the backend host.

## Current API Scope

- `GET /api/v1/health`
- `POST /api/v1/conversation/message`
- `POST /api/v1/conversation/stream`
- `POST /api/v1/conversation/attachment`
- `POST /api/v1/asr/transcribe`
- `GET /api/v1/parent/policy`
- `POST /api/v1/parent/policy`
- `GET /api/v1/parent/reports/{child_id}`
- `GET /api/v1/parent/report/today`
- `GET /api/v1/memories/{child_id}`
- `POST /api/v1/tts/xiaobaohu`
- `GET /media/tts/{voice_version}/{cache_key}.wav`

## XiaoBaiHu TTS Endpoint

The backend now owns the official 小白狐 voice path. Android should not call
MiMo directly and must not store any TTS API key.

For real QA, use the configured 小白狐 TTS provider. The endpoint shape is:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/tts/xiaobaohu \
  -H 'content-type: application/json' \
  -d '{"text":"我们先看这道题在问什么。","emotion":"hint","voiceVersion":"xiaobaohu_v01"}'
```

Expected response shape:

```json
{
  "audioUrl": "/media/tts/xiaobaohu_v01/<cache_key>.wav",
  "duration": 0.25,
  "text": "我们先看这道题在问什么。",
  "emotion": "hint",
  "voiceVersion": "xiaobaohu_v01",
  "provider": "<actual_provider>",
  "model": "<actual_model>",
  "cacheHit": false
}
```

Important paths:

```text
backend/assets/voices/xiaobaohu_voice_v01.wav
backend/storage/tts_cache/
```

`backend/assets/voices/xiaobaohu_voice_v01.wav` is the server-side voice clone
reference sample. It is not an Android asset and is not served through
`/media/tts`.

`backend/storage/tts_cache/` stores generated wav files and metadata. Generated
cache files are ignored by git. The media route serves only `.wav` files and
does not serve metadata JSON or the voice sample.

Example TTS environment for explicit local configuration:

```bash
export CHILD_AI_TTS_PROVIDER=mimo
export CHILD_AI_CONVERSATION_TTS_ENABLED=true
export CHILD_AI_MIMO_TTS_ENABLED=true
export CHILD_AI_MIMO_TTS_API_KEY=""
export CHILD_AI_MIMO_TTS_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
export CHILD_AI_MIMO_TTS_MODEL=mimo-v2.5-tts-voiceclone
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT=true
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED=true
```

Only enable MiMo VoiceClone in a local ignored `.env` or temporary shell after
explicitly accepting child-text transmission and retention policy checks:

```bash
export CHILD_AI_TTS_PROVIDER=mimo
export CHILD_AI_MIMO_TTS_ENABLED=true
export CHILD_AI_MIMO_TTS_API_KEY="<temporary key>"
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT=true
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED=true
```

For a real local MiMo VoiceClone smoke test, keep the API key in `.env` or the
shell only, start the backend with the same TTS env, then run:

```bash
TTS_SMOKE_BASE_URL=http://127.0.0.1:8000 bash scripts/smoke_mimo_tts.sh
```

The script checks the server-side voice sample, prints only the API-key length,
calls `POST /api/v1/tts/xiaobaohu`, downloads the generated `/media/tts/...wav`,
and then verifies that `/api/v1/conversation/message` can return a non-empty
`reply.audio_url`. It uses fake smoke text only.

Current real MiMo VoiceClone adapter notes from 2026-05-20 smoke:

```text
endpoint: /chat/completions
request audio: top-level audio.format=wav and audio.voice=data:audio/wav;base64,...
response audio: choices[0].message.audio.data
voice sample sha256: 8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40
```

`TtsDataPolicyGuard` runs before any external TTS provider call. If the guard
blocks, the endpoint returns a clear error and conversation can still return
text with `audio_url=null`. The conversation integration is also gated by
`CHILD_AI_CONVERSATION_TTS_ENABLED=false` by default.

## Streaming And Ops Roadmap

The legacy conversation path is intentionally still synchronous:

```text
child input -> full LLM reply -> full TTS audio -> response text + audio_url
```

This remains the Android fallback. The backend now also exposes a separate
Streaming v1 skeleton without breaking the existing API:

```text
POST /api/v1/conversation/stream
```

Current stream behavior:

```text
1. Keep `/api/v1/conversation/message` for fallback and regression safety.
2. Continue routing through SafetyEngine, IntentClassifier, SceneOrchestrator,
   ChildAgentRuntime, ModelRegistry, and TtsDataPolicyGuard.
3. Return `application/x-ndjson` events with session_started, route_decision,
   text_delta, sentence_ready, tts_started, audio_ready, text_final, done/error.
4. Split text into sentence/chunk events and interleave TTS per segment:
   `text_delta`, `sentence_ready`, `tts_started`, `audio_ready/error`.
5. Emit `text_final` after all segment TTS attempts, then `done`.
6. Use sentence-level pseudo streaming first; true MiMo streaming is not assumed.
7. TTS failure must not fail the text stream. Android should not mix system TTS
   voice into the same stream segment when a remote segment fails; it should
   keep the text visible and continue later remote segments.
8. `app.stream_timing` logs request_id, session_id_hash, active_scene,
   first_text_ms, first_tts_start_ms, first_audio_ms, stream_total_ms,
   text_segment_count, tts_segment_count, audio_segment_count,
   tts_error_count, and error_type.
```

Local stream smoke:

```bash
curl -sS --no-buffer -X POST http://127.0.0.1:8000/api/v1/conversation/stream \
  -H 'content-type: application/json' \
  -H 'X-Request-ID: stream-readme-smoke-001' \
  -d '{"child_id":"stream_demo_child","session_id":"stream_demo_session","input":{"type":"text","text":"我想聊恐龙","attachments":[]},"client_context":{"device_time":"2026-05-21T16:35:00+08:00","timezone":"Asia/Shanghai","app_mode":"child"},"stream_options":{"include_tts":false,"client_turn_id":"readme_smoke_001"}}'
```

Android stream client, progressive bubble rendering, and audio segment queue are
not implemented in this backend slice.

The first backend Ops P0 slice is now in place. It is intentionally local-first
and does not use a third-party APM or external log platform:

```text
1. Every HTTP response includes `X-Request-ID`.
2. Safe incoming `X-Request-ID` values are reused; illegal or overlong values
   are replaced.
3. Backend logs are JSON lines and carry request_id context.
4. `app.request_timing` logs request_finished/request_failed with method, path,
   status_code, elapsed_ms, and error_type.
5. `app.model_timing` logs model_call_finished with task_type, provider, model,
   elapsed_ms, fallback_used, policy_blocked, error_type, child_id_hash, and
   session_id_hash.
6. `app.tts_timing` logs tts_call_finished with provider, model, voice_version,
   emotion, cache_hit, elapsed_ms, audio_bytes, text_chars, cache_key_prefix,
   and error_type.
7. `GET /api/v1/health/detail` reports postgres, tts_cache, 小白狐 voice sample,
   and MiMo TTS config status.
```

Allowed log content:

```text
request_id, method, path, status_code, elapsed_ms
provider, model, task_type, fallback_used, policy_blocked, cache_hit
voice_version, emotion, audio_bytes, text_chars, cache_key_prefix
child_id_hash, session_id_hash, error_type
```

Forbidden log content:

```text
API keys, Authorization headers, full child text, full prompt,
full parent_message_raw, full image descriptions, raw audio/photo paths,
full TTS text, full reply text, and signed audioUrl query parameters.
```

Local health detail:

```bash
curl -sS http://127.0.0.1:8000/api/v1/health/detail
```

`/api/v1/health` remains a lightweight process-alive check. `/health/detail`
may return `"status":"degraded"` when PostgreSQL is unavailable, the TTS cache
is not writable, the 小白狐 voice sample is missing, or MiMo TTS is enabled but
missing key/policy configuration. It never returns the API key, database URL, or
voice sample contents.

Streaming v1 will reuse the same request_id and provider timing fields, then add
stream-specific `first_text_ms`, `first_tts_start_ms`, `first_audio_ms`, and
`stream_total_ms`.

## ASR v1: Local SenseVoice + MiMo Fallback

ASR research and integration design are documented in:

```text
docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md
docs/ASR_INPUT_RESEARCH_V0_1.md
docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md
```

Current backend status:

```text
1. ASR v1 target is backend local-first ASR: sherpa-onnx + SenseVoice-Small int8.
2. Android records/uploads to the backend and child mode auto-sends a non-empty transcript; `requiresConfirmation=true` pending transcript UI is kept only for DevSettings / father debugging.
3. Android must not call MiMo directly and must not store MiMo API keys.
4. `POST /api/v1/asr/transcribe` is mounted; active ASR QA must verify the selected provider in the response instead of assuming recording upload equals real recognition.
5. `local_sensevoice` is implemented as a formal provider and lazy-loads the ONNX model only on first recognition.
6. If local SenseVoice raises a provider/config/runtime error, `AsrService` can fall back to `CHILD_AI_ASR_FALLBACK_PROVIDER`; the operational default is `mimo`.
7. MiMo ASR fallback remains controlled by policy gates. Real child audio external transmission still requires father authorization and all ASR policy flags.
8. No real child audio should be used in development smoke; use fake/smoke audio or non-child test audio only.
9. Raw audio must not be stored in the database, logs, long-term memory, docs, tests, or git.
```

Example ASR environment for explicit local configuration:

```bash
export CHILD_AI_ASR_PROVIDER=local_sensevoice
export CHILD_AI_ASR_FALLBACK_PROVIDER=mimo
export CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true
export CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH=backend/models/asr/sensevoice/model.int8.onnx
export CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH=backend/models/asr/sensevoice/tokens.txt
export CHILD_AI_LOCAL_SENSEVOICE_NUM_THREADS=4
export CHILD_AI_LOCAL_SENSEVOICE_USE_ITN=true
export CHILD_AI_LOCAL_SENSEVOICE_LANGUAGE=zh
export CHILD_AI_MIMO_ASR_ENABLED=true
export CHILD_AI_MIMO_ASR_API_KEY=""
export CHILD_AI_MIMO_ASR_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
export CHILD_AI_MIMO_ASR_MODEL=mimo-v2.5
export CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true
export CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true
export CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true
```

Install the optional local ASR runtime:

```bash
cd backend
python -m pip install -e ".[dev,asr-local]"
```

Install SenseVoice-Small int8 ONNX model files under the ignored model
directory:

```bash
mkdir -p backend/models/asr/sensevoice /tmp/child-ai-asr-models
curl -L \
  -o /tmp/child-ai-asr-models/sensevoice.tar.bz2 \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
tar -xjf /tmp/child-ai-asr-models/sensevoice.tar.bz2 -C /tmp/child-ai-asr-models
cp /tmp/child-ai-asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx backend/models/asr/sensevoice/model.int8.onnx
cp /tmp/child-ai-asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt backend/models/asr/sensevoice/tokens.txt
```

Enable local-first ASR:

```bash
export CHILD_AI_ASR_PROVIDER=local_sensevoice
export CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true
export CHILD_AI_ASR_FALLBACK_PROVIDER=mimo
```

For local development without cloud fallback, use:

```bash
export CHILD_AI_ASR_FALLBACK_PROVIDER=mock
```

Local SenseVoice smoke harness:

```bash
python scripts/check_local_sensevoice_asr_status.py \
  --audio /path/to/non_child_test.wav \
  --fallback mock \
  --expect-pass \
  --output docs/LOCAL_ASR_SENSEVOICE_SMOKE_V0_1.md
```

Result semantics:

- `PASS`: `numpy` and `sherpa_onnx` import, `model.int8.onnx` and `tokens.txt`
  exist, and the ASR response provider is `local_sensevoice` with status `ok` or
  `needs_retry`.
- `BLOCKED`: dependency/model/tokens/audio are missing, or local primary failed
  and only a fallback provider responded. `fallback=mock` can verify fallback
  plumbing, but it is not a local SenseVoice pass.
- `FAIL`: unexpected provider/API failure, route crash, or raw audio/base64 leak.

The report records provider/model/status, elapsed time, and transcript length
only. It does not include audio data, base64, full transcript text, model files,
or child recordings. The 2026-05-23 local run used a macOS synthetic non-child
Chinese WAV and returned `provider=local_sensevoice`, `model=model.int8.onnx`,
`status=ok`; this validates the local provider path, not real child accuracy or
Android device QA.

MiMo fallback uses `mimo-v2.5` by default. Do not use the text conversation
model `mimo-v2.5-pro` for ASR.

MiMo fallback fake-audio smoke script:

```bash
set -a
source .env
set +a
CHILD_AI_ASR_PROVIDER=mimo \
CHILD_AI_MIMO_ASR_ENABLED=true \
CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true \
CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true \
CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true \
CHILD_AI_ASR_SMOKE_WAV=/path/to/fake_or_smoke_audio.wav-or.m4a \
ASR_SMOKE_BASE_URL=http://127.0.0.1:8000 \
bash scripts/smoke_mimo_asr.sh
```

The smoke script accepts `.wav` or `.m4a` smoke audio. `.m4a` is converted to
16 kHz mono WAV before upload so the smoke path matches the Android recorder
and the MiMo spec's `data:audio/wav;base64,...` input requirement. The script
prints only status/provider/model/duration/confidence/errorCode. It does not
print the API key, base64 audio, full transcript, request body, response body,
or audio path.

Do not enable MiMo ASR fallback with real child audio until father authorization,
retention/deletion/no-training terms, and all ASR policy flags are confirmed.

### ASR QA artifact rule

Android ASR UI code does not mean real ASR is enabled. Before asking for real
speech-recognition QA, verify the running backend is not using mock ASR and
record whether the provider is local or cloud fallback:

```bash
set -a
source .env
set +a
python3 - <<'PY'
import os
for key in [
    "CHILD_AI_ASR_PROVIDER",
    "CHILD_AI_ASR_FALLBACK_PROVIDER",
    "CHILD_AI_LOCAL_SENSEVOICE_ENABLED",
    "CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH",
    "CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH",
    "CHILD_AI_MIMO_ASR_ENABLED",
    "CHILD_AI_MIMO_ASR_API_KEY",
    "CHILD_AI_MIMO_API_KEY",
    "CHILD_AI_MIMO_TTS_API_KEY",
    "CHILD_AI_MIMO_ASR_MODEL",
    "CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO",
    "CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED",
    "CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED",
]:
    value = os.getenv(key, "")
    print(f"{key}={'present' if 'KEY' in key and value else value or 'missing'}")
PY
```

If `CHILD_AI_ASR_PROVIDER` points to a non-real test double, the artifact can only test recording,
upload, confirmation UI, and graceful retry messaging. It must not be described
as a real recognition test. For local ASR QA, verify the backend response shows
`provider=local_sensevoice` and uses the intended ONNX file. For cloud fallback
QA, verify the smoke output shows `provider=mimo` and `model=mimo-v2.5`.

The existing standard MiMo fallback status check is:

```bash
bash scripts/check_asr_real_status.sh
```

`ASR_STATUS=mock_only` means only a non-real ASR test-double path is active.
`ASR_STATUS=policy_blocked` means MiMo ASR is selected but required policy/key
env is incomplete. `ASR_STATUS=mimo_smoke_pass` is the only script status that
can be described as a successful real MiMo fallback smoke.

ASR does not require a separate key by default. The backend resolves MiMo ASR
credentials in this order:

```text
1. CHILD_AI_MIMO_ASR_API_KEY
2. CHILD_AI_MIMO_API_KEY
3. CHILD_AI_MIMO_TTS_API_KEY
```

Use `CHILD_AI_MIMO_ASR_API_KEY` only when ASR needs an explicit override.

## Safety Notes

- `high` / `critical` input routes to `safety.guardian` with
  `requires_parent_attention=true`.
- Automatic safety memory created from `safety.guardian` is parent-visible and
  requires parent attention, but normal runtime retrieval calls
  `MemoryService.retrieve(..., include_safety=false)` so safety memories are not
  mixed into ordinary child-facing memory context.
- `watch` input, such as fictional peer bullying test text, routes to
  `safety.gentle_checkin` by default. It uses calm wording, encourages telling
  a parent or teacher, and does not force parent attention. The automatic memory
  hook records a parent-visible observation summary, not a raw transcript.
- Low-risk privacy questions route to `privacy.boundary` and remind the child
  not to share addresses, phone numbers, school names, or photos with AI or
  strangers. The automatic memory hook stores only the generic boundary reminder,
  not the specific address, phone number, school name, or photo content.
- Low-energy emotion expressions, such as not wanting to talk, remain in normal
  check-in/emotion support instead of `safety.guardian`.
- Learning help refuses direct final answers and asks for problem understanding or first-step thinking.
- Parent goals may influence wording, but they do not override child safety rules.
- Tests and demos must use fake child IDs and safe synthetic content only.
