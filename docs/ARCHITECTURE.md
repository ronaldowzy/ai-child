# Architecture

`ai-child` is split into an Android client and a FastAPI backend. The backend is
the policy and provider boundary: Android captures input and renders state,
while the backend owns model calls, prompt assembly, safety checks, ASR/TTS
provider configuration, media handling, and parent-facing summaries.

## High-Level Flow

```text
Android child client
  -> backend API
  -> ASR / safety / intent / scene orchestration
  -> model provider registry
  -> TTS / media cache
  -> structured memory and parent report services
  -> Android rendering and audio playback
```

## Repository Layout

```text
android/
  app/src/main/java/com/childai/companion/
backend/
  app/api/
  app/core/
  app/domain/
  app/providers/
  app/repositories/
  app/services/
  app/tests/
docs/
scripts/
deploy/
```

## Backend Boundaries

- API routes handle HTTP input/output and call services.
- Services hold business behavior and safety-critical orchestration.
- Providers isolate external ASR, TTS, vision, and model integrations.
- Repositories isolate persistence.
- Prompt assembly goes through `PromptManager`.
- Safety classification goes through `SafetyEngine`.
- Model calls go through `ModelRegistry`.

## Android Boundaries

- Android does not store model provider credentials.
- Android sends voice/photo/text input to backend APIs.
- Android renders backend conversation state, mascot state, and audio URLs.
- Parent-facing entry points are treated separately from the child surface.

## Safety and Privacy Boundaries

The backend is responsible for:

- provider data-policy gates;
- prompt safety constraints;
- media path validation;
- debug trace redaction expectations;
- parent policy and child profile handling.

See `SAFETY_AND_PRIVACY.md` for public release rules.
