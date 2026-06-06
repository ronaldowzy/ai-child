# Safety and Privacy

`ai-child` is designed as a parent-governed child AI companion prototype. The
repository should remain useful to developers without exposing private family
data or encouraging unsafe child-facing product patterns.

## Child-Safety Product Boundaries

The project avoids:

- positioning AI as a child's only friend or secret confidant;
- asking children to hide things from parents, teachers, or trusted adults;
- addictive loops such as streak pressure, rankings, gacha, hunger mechanics,
  or fear-of-missing-out prompts;
- direct final answers for learning support when guided thinking is more
  appropriate;
- open-ended stranger social features.

High-risk child inputs should encourage the child to involve a parent, teacher,
or trusted adult and should surface parent attention where appropriate.

## Data-Minimization Rules

Public examples and tests must use synthetic data. Do not commit:

- real child names, family names, phone numbers, addresses, or school details;
- raw family transcripts or raw model prompts from private testing;
- child audio, photos, screenshots, or generated reports from real use;
- API keys, `.env`, databases, generated TTS cache, or model weights.

## Provider Boundary

Android does not store model provider API keys. External model, ASR, TTS, and
vision providers are called through the backend behind explicit configuration
and data-policy gates.

Local-first ASR is preferred where possible. Cloud fallback paths should remain
feature-flagged, policy-gated, and easy to disable.

## Logging and Debug Traces

Debug traces are useful for development but can become sensitive quickly. Public
logs should be redacted before being committed or attached to issues. Raw prompt
appendices from private testing are not public documentation.

## Public Release Gate

Before changing the repository to public:

1. run a secret scan;
2. remove real prompt traces and child/family data;
3. verify ignored local artifacts are not tracked;
4. review voice, image, screenshot, and mascot assets for redistribution rights;
5. consider history cleaning if sensitive files were committed while private.
