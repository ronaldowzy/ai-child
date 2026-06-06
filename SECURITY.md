# Security Policy

`ai-child` handles safety-sensitive flows around child-facing conversation,
voice input, images, parent controls, and external model providers.

## Supported Versions

The public repository currently tracks active development on `main`. Security
fixes should target `main` unless a maintainer has created a release branch.

## Reporting a Vulnerability

Do not open a public issue containing secrets, real child data, raw prompts,
audio, screenshots, or exploit details.

Please contact the repository owner privately through GitHub profile contact
options. Include:

- affected area;
- reproduction steps using synthetic data;
- impact assessment;
- whether credentials, child data, media, or provider logs may be involved.

## Sensitive Data Rules

- Never commit `.env`, API keys, local databases, model weights, generated TTS
  cache, real child media, or real family transcripts.
- Use `.env.example` and synthetic fixtures for public examples.
- Keep model provider keys and data policy flags on the backend.
- Sanitize logs before attaching them to issues or pull requests.

## Safety-Critical Areas

Please use extra review for changes to:

- prompt assembly and safety prompts;
- ASR/TTS/vision data-policy gates;
- parent authentication and parent controls;
- child profile and memory handling;
- media upload, cache, and serving paths;
- logging and debug trace output.
