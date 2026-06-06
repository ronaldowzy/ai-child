# Roadmap

This roadmap describes public OSS priorities for `ai-child`. Product-specific
family beta planning remains in the detailed Chinese planning documents.

## Current Focus

`ai-child` is an open-source reference implementation for a child-safe AI
companion architecture:

- Android child-facing client;
- FastAPI backend mediation layer;
- local-first ASR with controlled cloud fallback;
- backend-only model, TTS, and vision provider integration;
- parent-governed configuration and reports;
- safety guardrails for child-facing conversation.

## Near-Term Public OSS Work

1. Public repository hygiene
   - Keep secrets, model weights, raw media, private transcripts, and real child
     data out of git.
   - Maintain public-safe examples and issue templates.

2. CI and test reliability
   - Run backend tests and lint in CI.
   - Run Android unit tests in CI.
   - Keep safety-critical behavior covered by focused tests.

3. Safety and privacy documentation
   - Document provider data-policy gates.
   - Document prompt safety boundaries.
   - Document media upload, cache, and retention assumptions.

4. Local-first voice stack
   - Keep SenseVoice local ASR as the preferred low-latency path.
   - Keep cloud ASR/TTS paths explicit, feature-flagged, and policy-gated.

5. Developer onboarding
   - Improve setup scripts and diagnostics.
   - Add synthetic demo flows that do not require private data.

## Longer-Term Directions

- Stronger regression tests for prompt safety and parent-report boundaries.
- Better observability without logging sensitive text or media.
- Sanitized screenshots and demo assets for public documentation.
- Release notes and versioned public demo packages.
