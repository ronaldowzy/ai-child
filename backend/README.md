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
- Normalizes child-facing model replies for voice-first use: short natural
  sentences, no Markdown/list formatting, and usually one main question.
- Returns child-facing reply metadata for future voice and white-fox animation
  work: `voice_enabled`, optional `audio_url`, `emotion`, and `agent_motion`.

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
variables and never write the real key to `.env`, docs, tests, Android, or git:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_API_KEY="<temporary key>"
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=true
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
export CHILD_AI_MIMO_TIMEOUT_MS=12000
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

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
