# Model Debug Trace v0.1

Status: DEV-TRACE-1 implemented for local dev/test only; DEV-TRACE-2 mock
synthetic scenario runner and review report added; DEV-TRACE-3 real MiMo
opt-in synthetic trace review added.

## 1. Scope

`model_debug_traces` is a temporary local PostgreSQL/SQLite-compatible table for
analyzing prompt quality during the current family testing phase.

It records calls that pass through `ModelRegistry.generate()` so product and
prompt review can inspect what was sent to the model and what came back.

## 2. Non-goals

- No Android UI.
- No admin dashboard.
- No cloud sync.
- No production retention policy.
- No prompt scoring.
- No true LLM streaming, CameraX, E2-B durable recall, Android QA, or
  production provider smoke automation.

## 3. Enablement

Default is off:

```text
CHILD_AI_MODEL_DEBUG_TRACE_ENABLED=false
CHILD_AI_MODEL_DEBUG_TRACE_FULL_TEXT=true
CHILD_AI_MODEL_DEBUG_TRACE_MAX_TEXT_CHARS=20000
```

Local opt-in:

```bash
export CHILD_AI_MODEL_DEBUG_TRACE_ENABLED=true
export CHILD_AI_MODEL_DEBUG_TRACE_FULL_TEXT=true
export CHILD_AI_MODEL_DEBUG_TRACE_MAX_TEXT_CHARS=20000
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

The flag only controls trace persistence. It never changes provider selection,
fallback behavior, policy blocking, or child-facing replies.

## 4. Recorded Fields

The table records:

- `request_id`
- `task_type`
- `profile_name`
- `provider_name`
- `model_name`
- `child_id` / `session_id`
- `child_id_hash` / `session_id_hash`
- `request_messages_json`
- `request_input_text`
- `request_context_json`
- `request_metadata_json`
- `request_params_json`
- `response_text`
- `response_structured_output_json`
- `response_metadata_json`
- `fallback_used`
- `policy_blocked`
- `error_type`
- `error_detail`
- `elapsed_ms`
- `trace_source`
- `environment`

This covers `child_chat`, opening greeting, parent report, vision/OCR, safety,
intent, and other model tasks that use `ModelRegistry.generate()`.

## 5. Data Filtering

Allowed in this local trace:

- Full text prompts.
- System/user/assistant messages.
- `input_text`.
- Model `response_text`.
- Structured output and metadata.
- Local test child/session ids.

Always filtered:

- API keys.
- Authorization headers.
- Bearer tokens.
- `.env` contents.
- Raw audio bytes.
- Raw image bytes.
- Base64 audio/image payloads.
- Provider raw HTTP headers.

Multimodal message data URIs and long base64-looking strings are replaced with:

```text
[raw_media_omitted]
```

Secret-like fields are replaced with:

```text
[redacted]
```

Long text is truncated according to
`CHILD_AI_MODEL_DEBUG_TRACE_MAX_TEXT_CHARS` and marked with
`...[truncated]`.

## 6. Failure Semantics

Trace persistence is best-effort:

- DB unavailable: model call still returns or raises exactly as before.
- Repository exception: warning log only.
- Trace failure log contains only request/task/hash/error type context.

## 7. Inspect And Clear

Show recent traces:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/show_model_debug_traces.py --limit 20
```

Clear traces:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/clear_model_debug_traces.py
```

Repository tests also cover `ModelDebugTraceRepository.clear()`.

## 8. Synthetic Scenario Review

Run a repeatable mock-provider trace review from the repository root:

```bash
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/run_model_trace_scenarios.py
```

The runner:

- Forces mock providers and trace enablement for its own process.
- Clears `model_debug_traces` before execution.
- Runs synthetic opening, child_chat, and parent_report scenarios.
- Verifies child_chat model traces were actually written.
- Marks opening and parent_report as `deterministic_default` because the family
  MVP no longer calls the model for those default paths.
- Writes `docs/MODEL_TRACE_SCENARIO_REVIEW_V0_1.md`.

The generated review is for prompt and contract analysis only. It is not real
child QA, not real MiMo output quality, and not Android device validation.

Run a real MiMo synthetic text-only review with explicit opt-in:

```bash
CHILD_AI_MIMO_API_KEY=... \
/opt/homebrew/bin/conda run --no-capture-output -n child-ai \
  python scripts/run_model_trace_scenarios.py \
    --provider mimo \
    --output docs/MODEL_TRACE_REAL_PROVIDER_REVIEW_V0_1.md
```

The real-provider mode:

- Is never the default.
- Loads local `.env` values into the runner process only and does not print
  secrets.
- Applies a temporary process env overlay for child_chat real-provider calls.
- Keeps opening and parent_report on deterministic defaults; they are not real
  provider quality evidence in this runner.
- Runs synthetic text scenarios only; it does not use real child audio, images,
  photos, Android, CameraX, ASR, TTS, or vision.
- Writes `docs/MODEL_TRACE_REAL_PROVIDER_REVIEW_V0_1.md`.
- Reports `REAL_PROVIDER_BLOCKED: missing CHILD_AI_MIMO_API_KEY` when no key is
  available instead of falling back to mock and calling it pass.

The 2026-05-23 real MiMo synthetic run reached `REAL_PROVIDER_SMOKE: PASS` with
provider/model `mimo/mimo-v2.5-pro` for child_chat. After PD-052, ParentReport
is model-first again, so fresh trace reviews should expect `parent_report`
traces and must not treat mock/deterministic fallback as formal report success.
Opening remains deterministic by default and is reported separately from model
quality evidence.

## 9. Compliance Boundary

This is not a production child-data policy and not an app-store/cloud-ready
observability design. Before any cloud deployment or public release, prompt and
response tracing must be redesigned with child-data compliance, retention,
access control, deletion, export, and parental consent review.
