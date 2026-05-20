# Backend

FastAPI backend for the v0.1 child AI growth agent MVP.

The current backend is intentionally local-first and mock-first:

- Uses `MockModelProvider` by default.
- Does not call real model, OCR, vision, or external network services in tests.
- Keeps all child-facing AI decisions behind backend services such as `SafetyEngine`, `IntentClassifier`, `SceneOrchestrator`, `PromptManager`, and `ModelRegistry`.
- Routes child-facing replies through `ChildAgentRuntime`: `SceneOrchestrator`
  decides the scene strategy and safe fallback reply, `PromptManager` composes
  the prompt, `ModelRegistry` generates the child chat response, and
  `SafetyEngine.classify_output()` checks the output before return.
- Retrieves non-safety structured memory before `ChildAgentRuntime`, and writes
  rule-based conversation memory after routing. Memory evidence uses summary
  sources only; raw chat, full transcripts, raw audio, and raw photos are not
  stored as long-term evidence.
- Treats child chat as open-ended conversation. Time periods and scenes provide
  context, safety boundaries, and fallback replies; they should not force every
  ordinary message into a fixed script.
- Uses `ConversationHistoryService` for short-term, in-memory recent turns so
  ordinary chat can keep context within one running backend process. This is not
  a durable chat database; service restart clears it, and full chat transcripts
  are not written to long-term memory or parent reports.
- Normalizes child-facing model replies for voice-first use: short natural
  sentences, no Markdown/list formatting, and usually one main question.
- Returns child-facing reply metadata for future voice and 小白狐 animation
  work: `voice_enabled`, optional `audio_url`, `emotion`, and `agent_motion`.
- Speech recognition remains Android confirm-before-send: confirmed text is
  sent to the existing conversation API, and raw child audio is not uploaded by
  default.
- 小白狐 voice output now has a backend TTS path: `POST /api/v1/tts/xiaobaohu`
  can generate or return a cached wav URL. The default provider is mock and
  never calls external services. MiMo VoiceClone is disabled until explicit
  local environment variables and the TTS data policy gate allow child text
  transmission. Android now prefers `reply.audio_url` playback and falls back
  to local TextToSpeech or text if remote audio fails.

If Android replies look like fixed templates such as “听起来可以聊”, the backend
is probably running with the default mock provider. For real Mimo chat, restart
the backend with the temporary environment variables in the Mimo section below;
do not put the real API key into git, Android, docs, tests, or screenshots.

## Current Voice And Presentation Contract

The backend remains the decision and safety boundary. Android may use local
`SpeechRecognizer` later, and now uses remote audio playback plus TextToSpeech
fallback for voice output, but child-facing content still flows through:

```text
SafetyEngine -> IntentClassifier -> SceneOrchestrator -> PromptManager -> ModelRegistry -> output safety check
```

Current backend contract:

- Accept confirmed text through `POST /api/v1/conversation/message`.
- Treat v1 speech input as confirm-before-send; hands-free conversational mode
  is a future product phase and should not change the v1 backend contract.
- Do not require raw audio upload for v0.2 voice input.
- Keep external audio and child text transmission disabled unless a confirmed
  product decision and provider gate review explicitly allow it.
- Return `reply.voice_enabled`, optional `reply.audio_url`, `reply.emotion`, and
  `reply.agent_motion` for Android TTS and 小白狐 presentation.
- Use `POST /api/v1/tts/xiaobaohu` for backend-generated 小白狐 speech audio.
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
  privacy-boundary summaries, parent report visibility, and safety-memory
  retrieval isolation

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

## Local PostgreSQL Persistence

The v0.1-dev persistence target is local PostgreSQL for family testing. DB1-A
adds the database foundation only; current business services still use their
existing in-memory repositories until the B2-B5 migration steps wire them in.

Local dev database:

```bash
docker compose -f docker-compose.local.yml up -d
bash scripts/db_migrate.sh
```

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
tts_cache_records
```

Data boundary:

- This is local family-use storage, not a cloud multi-tenant production design.
- Conversation text may be stored locally for context, review, and parent report
  material after the B3 migration step.
- Raw audio files, raw photos, API keys, model keys, and debug internals must
  not be written to PostgreSQL.
- `tts_cache_records` stores hashes and cache metadata, not full sensitive TTS
  input text.
- Any future cloud deployment or app-store release requires a separate child
  data compliance review before enabling remote persistence.

## Optional Xiaomi Mimo Provider

v0.1 remains mock-first. A Xiaomi Mimo OpenAI-compatible provider can be configured for controlled local testing, but it is disabled by default and falls back to mock on provider/configuration failure.

Use environment variables only; never commit real API keys:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
export CHILD_AI_MIMO_MODEL=mimo-v2.5-pro
export CHILD_AI_MIMO_API_KEY="..."
```

For child-facing traffic, do not enable real external transmission until the safety/data-retention review is complete:

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

`scripts/dev_backend.sh` loads the root `.env` when it exists, then starts
uvicorn. This is only for local development; `.env` must stay ignored and must
not be shared.

Only use fictional child IDs and test text in this mode. Keep
`CHILD_AI_MIMO_ALLOW_IMAGE=false` and `CHILD_AI_MIMO_ALLOW_AUDIO=false` unless a
separate review explicitly allows those data types.

`ModelRegistry.generate()` enforces this as a code-level gate before any
OpenAI-compatible provider call. When request metadata marks
`contains_child_data=true`, an external profile must have both
`allow_child_data=true` and `retention_policy_checked=true`; otherwise it falls
back to the mock profile without calling the external provider. Metadata
`contains_image=true` and `contains_audio=true` also require `allow_image=true`
and `allow_audio=true`. Mock providers are not blocked by this external
transmission gate.

The child-facing runtime always marks child chat model requests with
`contains_child_data=true`. If prompt composition fails, the model registry
blocks or falls back from an external provider, the model call fails, the model
returns empty text, output safety is `high`/`critical`, or a learning-scene
model output appears to give a direct final answer, the runtime returns the
existing `SceneRouteDecision.reply_text` fallback instead of model text. This
keeps the default path mock-first and preserves a deterministic safe reply for
each routed scene.

Output safety also blocks model replies that create secret relationships,
isolate the child from trusted adults, or imply the AI is the child's only or
best friend. These checks run after model generation and before the response is
returned to Android.

The Android app never stores model API keys. All model configuration belongs on the backend host.

## Current API Scope

- `GET /api/v1/health`
- `POST /api/v1/conversation/message`
- `POST /api/v1/conversation/attachment`
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

Default behavior is local and mock-only:

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
  "provider": "mock",
  "model": "mock-tts-v0",
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

Default TTS environment:

```bash
export CHILD_AI_TTS_PROVIDER=mock
export CHILD_AI_CONVERSATION_TTS_ENABLED=false
export CHILD_AI_MIMO_TTS_ENABLED=false
export CHILD_AI_MIMO_TTS_API_KEY=""
export CHILD_AI_MIMO_TTS_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
export CHILD_AI_MIMO_TTS_MODEL=mimo-v2.5-tts-voiceclone
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT=false
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED=false
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

The current conversation path is intentionally still synchronous:

```text
child input -> full LLM reply -> full TTS audio -> response text + audio_url
```

This is good enough for smoke tests, but recent Redmi K60 testing shows that it
creates visible wait time even after Android's read timeout was raised. The next
backend milestone is to design and then add a separate streaming endpoint
without breaking the existing API:

```text
POST /api/v1/conversation/stream
```

Planned stream behavior:

```text
1. Keep `/api/v1/conversation/message` for fallback and regression safety.
2. Continue routing through SafetyEngine, IntentClassifier, SceneOrchestrator,
   ChildAgentRuntime, ModelRegistry, and TtsDataPolicyGuard.
3. Emit text delta events as soon as possible.
4. Split text into sentence/chunk events and generate TTS segments.
5. Emit audio-ready events as each segment becomes available.
6. If MiMo VoiceClone does not support true audio streaming, use
   sentence-level pseudo streaming first.
7. TTS failure must not fail the text stream.
```

The ops foundation also needs local-development observability before stream work
gets deep:

```text
1. request_id / trace_id middleware.
2. structured request timing logs.
3. LLM and TTS provider timing.
4. health checks for PostgreSQL, TTS cache path, and MiMo config readiness.
5. logs and QA records that do not include API keys, raw audio, raw photos, or
   full child transcripts.
```

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
- Tests and demos must use fake child IDs and safe mock content only.
