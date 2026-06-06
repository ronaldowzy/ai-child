# Public Release Checklist

Use this checklist before switching the GitHub repository from private to
public.

## Must Pass

- [ ] Repository is on the intended public branch.
- [ ] `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and
      issue templates exist.
- [ ] Secret scan finds no API keys, tokens, `.env`, private database URLs, or
      production credentials.
- [ ] No real child names, family names, raw transcripts, raw prompts, real
      child audio, photos, or screenshots are tracked.
- [ ] Voice samples, mascot assets, and screenshots have been reviewed for
      public redistribution rights.
- [ ] Backend tests and lint pass, or known failures are documented before
      public announcement.
- [ ] Android unit tests pass, or known failures are documented before public
      announcement.
- [ ] GitHub repository description and topics are set.

## History Cleaning

Deleting a file in a normal commit does not remove it from Git history. If any
sensitive file was committed while the repository was private, create a clean
public branch or rewrite history before making the repository public.

Recommended options:

- create a sanitized orphan public branch and import only approved files;
- or use `git filter-repo` to remove sensitive paths from history, then force
  push before the first public release.

Coordinate history rewriting carefully because it changes commit hashes for all
existing worktrees and branches.

## Suggested GitHub Metadata

Description:

```text
Open-source child-safe AI companion app prototype with Android client, FastAPI backend, local ASR, voice/vision, parent controls, and safety guardrails.
```

Topics:

```text
child-safety, ai-companion, android, fastapi, local-asr, voice-ai, parental-controls, privacy, kotlin, python
```
