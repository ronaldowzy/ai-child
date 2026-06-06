# Contributing

Thanks for helping improve `ai-child`. This repository is a child-safety
focused AI companion prototype, so contributions are reviewed with extra care
around privacy, safety, and testability.

## Development Setup

Use the repository scripts instead of ad-hoc commands:

```bash
bash scripts/doctor_local_env.sh
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/android_gradle.sh test
```

Backend code lives under `backend/`. Android code lives under `android/`.
Project rules for Codex or other coding agents are in `AGENTS.md`.

## Contribution Rules

- Do not commit real child names, family data, raw prompts, raw audio, photos,
  screenshots, API keys, local databases, or model weights.
- Use synthetic examples in tests and documentation.
- Keep AI behavior child-safe: no secrecy requests, no addictive loops, no
  "only friend" positioning, and no direct final answers for learning support.
- Add or update tests for behavior changes.
- Keep external provider credentials server-side only.

## Pull Request Checklist

- [ ] Relevant backend or Android tests pass locally.
- [ ] No real child data or secrets are included.
- [ ] New behavior is documented when it changes public APIs, safety behavior,
      prompts, or configuration.
- [ ] Any real provider path is feature-flagged and has a mock/test path.

## Reporting Problems

Use GitHub issues for bugs, feature requests, and documentation gaps. For
security or privacy issues, follow `SECURITY.md` instead of opening a public
issue with sensitive details.
