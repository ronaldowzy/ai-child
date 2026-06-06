# OSS Public Readiness Plan

This plan splits the fast public-readiness work into two independent branches
so packaging and engineering-health fixes can proceed in parallel.

## Branches

```text
oss-public-readiness
  Owner: public packaging and privacy cleanup
  Worktree: /Users/wzy/Documents/codex/ai_child_oss/public-readiness

oss-tests-ci
  Owner: test, lint, and CI stabilization
  Worktree: /Users/wzy/Documents/codex/ai_child_oss/tests-ci
```

## Public Packaging Track

Scope:

- add OSS community files;
- add public safety/privacy docs;
- add public roadmap and architecture summary;
- remove raw private prompt appendices from the current public tree;
- update README entry points;
- document the required public-release gate.

Out of scope:

- fixing backend or Android test failures;
- adding CI workflow files;
- changing runtime behavior.

## Test and CI Track

Scope:

- make backend tests pass;
- make backend lint pass;
- make Android unit tests pass;
- add or stage GitHub Actions CI;
- document any token limitation for pushing workflow files.

Out of scope:

- changing public positioning, license, contributing, security, or privacy docs;
- modifying private-data redaction decisions.

## Merge Order

1. Merge `oss-public-readiness` after reviewing the public tree and sensitive
   file scan.
2. Merge `oss-tests-ci` after tests and lint pass.
3. Re-run the public-release checklist on `main`.
4. Decide whether history cleanup is required before switching GitHub visibility
   from private to public.
