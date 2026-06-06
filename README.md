# ai-child

`ai-child` is an open-source reference implementation for a child-safe AI
companion application. It combines an Android client, a FastAPI backend,
local-first speech recognition, backend-mediated model/TTS/vision providers,
parent controls, and safety guardrails for child-facing interaction.

The project is not designed as an unrestricted chatbot for children. Its goal
is to demonstrate a practical architecture for parent-governed, privacy-aware,
and testable AI companion experiences.

中文项目说明见 [README.zh-CN.md](README.zh-CN.md).

## Why This Exists

Child-facing AI products need stronger defaults than generic chat apps:

- children should not be asked to keep secrets from parents, teachers, or
  trusted adults;
- learning support should guide thinking instead of simply giving final
  answers;
- high-risk child inputs should route toward adult support;
- provider API keys should stay off the device;
- raw child audio, photos, transcripts, and prompt traces should not be stored
  or published unnecessarily;
- engagement mechanics should avoid streak pressure, rankings, gacha, FOMO, or
  other addictive loops.

`ai-child` turns those constraints into backend services, Android state
handling, provider gates, tests, and public documentation.

## Core Capabilities

- Android child client with voice-first interaction.
- FastAPI backend with clear API/service/provider/repository boundaries.
- Local-first ASR using SenseVoice through `sherpa-onnx`, with controlled cloud
  fallback paths.
- Backend-only model, vision, and TTS provider integration.
- Streaming conversation events with text deltas and queued audio segments.
- Parent-managed child profile and parent policy settings.
- Parent report generation with safety and privacy boundaries.
- Mascot state mapping for a child-friendly companion surface.
- Test scripts and deployment scaffolding for local and server workflows.

## Architecture

```text
Android client
  -> FastAPI backend
  -> ASR / safety / intent / scene orchestration
  -> model provider registry
  -> TTS / media cache
  -> memory and parent-report services
  -> Android rendering and audio playback
```

Key directories:

```text
backend/   FastAPI backend, providers, services, tests
android/   Android client
docs/      product, safety, architecture, QA, and workflow docs
scripts/   local development, test, build, and release scripts
deploy/    server deployment notes
```

More detail:

- [Architecture](docs/ARCHITECTURE.md)
- [Safety and Privacy](docs/SAFETY_AND_PRIVACY.md)
- [Roadmap](docs/ROADMAP.md)
- [Public Release Checklist](docs/PUBLIC_RELEASE_CHECKLIST.md)

## Development

Use the repository scripts instead of ad-hoc commands. Some local shells may not
inherit Python, Java, or Android SDK paths correctly; the scripts normalize the
expected local setup.

```bash
bash scripts/doctor_local_env.sh
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/android_gradle.sh test
```

Backend development:

```bash
bash scripts/dev_backend.sh
bash scripts/demo_backend_scenarios.sh
bash scripts/e2e_local_api_check.sh
```

Android development:

```bash
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

## Safety and Data Rules

Do not commit:

- `.env` files, API keys, tokens, or production credentials;
- real child names, family data, raw transcripts, or raw prompt traces;
- child audio, photos, private screenshots, or generated reports from real use;
- local databases, model weights, generated TTS cache, or build artifacts.

Public tests and examples should use synthetic data only. See
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before opening
a pull request or issue.

## Project Status

The repository is in active prototype development. The current emphasis is on:

- public-safe documentation and repository hygiene;
- reliable backend and Android tests;
- safety regression coverage;
- local-first voice interaction;
- parent-governed configuration and reporting;
- sanitized demo and release materials.

This is not a production child-safety certification. Treat it as an engineering
reference and prototype for exploring safer child-facing AI application
patterns.

## License

MIT. See [LICENSE](LICENSE).
