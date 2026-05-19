# Backend

FastAPI backend for the v0.1 child AI growth agent MVP.

The current backend is intentionally local-first and mock-first:

- Uses `MockModelProvider` by default.
- Does not call real model, OCR, vision, or external network services in tests.
- Keeps all child-facing AI decisions behind backend services such as `SafetyEngine`, `IntentClassifier`, `SceneOrchestrator`, `PromptManager`, and `ModelRegistry`.

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
- high-risk safety guardian routing
- bedtime reflection
- parent goal influencing reply wording
- model fallback

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

- High-risk input routes before normal scene handling.
- Learning help refuses direct final answers and asks for problem understanding or first-step thinking.
- Parent goals may influence wording, but they do not override child safety rules.
- Tests and demos must use fake child IDs and safe mock content only.
