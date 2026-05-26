# PROMPT_AND_COPY_OWNERSHIP_RULES_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Purpose: define hard ownership rules for prompts, product wording, parent reports, and child-facing copy.

---

## 0. Why this document exists

Recent iterations showed a repeated failure mode:

```text
The master session identified a product/copy problem, then asked the code agent to “improve” or “strengthen” the prompt. The code agent implemented something functional but not sufficiently natural, parent-aware, or aligned with Chinese family usage.
```

This is no longer acceptable.

Prompt/copy design is a product-design responsibility, not an implementation-agent responsibility.

---

## 1. Hard ownership rule

The master session owns all product-sensitive language.

This includes:

```text
1. system prompts;
2. scene prompts;
3. child-facing AI behavior instructions;
4. parent report prompts;
5. parent report examples;
6. deterministic fallback wording;
7. child-facing UI copy;
8. parent-facing UI copy;
9. safety/privacy/learning wording;
10. mascot personality wording;
11. task documents that define any of the above.
```

Code agents own implementation only.

A code agent may:

```text
1. copy exact wording supplied by the master session;
2. wire supplied wording into code;
3. adjust escaping, indentation, localization wrappers, and tests;
4. report compile/test failures that require the master session to revise wording.
```

A code agent must not:

```text
1. invent prompt wording;
2. “improve” child-facing or parent-facing copy on its own;
3. rewrite parent report examples;
4. decide what a Chinese parent would naturally say;
5. decide psychological/educational boundaries;
6. replace a supplied phrase with a similar-sounding phrase without approval;
7. add teacher-like,客服-like,工程-like,监控-like wording;
8. add reward, streak, score, mission, dependency, or retention language.
```

---

## 2. Required format for future language tasks

Any task that touches prompts or product copy must include one of these:

```text
A. Exact replacement text supplied by the master session; or
B. A linked master-copy document containing the exact text to paste; or
C. A statement that the task is blocked until the master session supplies wording.
```

The phrase “improve the prompt” is not a valid implementation instruction.

The phrase “make it more natural” is not sufficient for a code agent.

The phrase “strengthen parent report prompt” is not sufficient unless exact replacement text is provided.

---

## 3. Review rule

When reviewing a code-agent submission that touches prompts or copy, reject it if:

```text
1. the code agent invented wording not present in the task or master-copy document;
2. the copy is merely semantically similar but changes product intent;
3. the wording sounds like a teacher report, customer-service notice, engineering log, monitoring report, or gamified retention hook;
4. the parent report exposes or invites interrogation about child-Xiaobaihu private interaction details;
5. child-facing copy includes backend/provider/ASR/error/policy/prompt/internal terminology.
```

---

## 4. Parent report special rule

Parent report wording is especially sensitive.

The master session must provide:

```text
1. the exact model system prompt or a master-copy prompt file;
2. good output examples;
3. bad output examples;
4. deterministic fallback wording;
5. forbidden parent-facing phrases;
6. visible-quality test expectations.
```

The code agent must only implement and test.

---

## 5. If wording is embedded in code

If the final wording lives inside a code file, the preferred workflow is:

```text
1. master session writes the exact prompt/copy in a docs master-copy file;
2. code agent copies it into the code file without redesigning it;
3. code agent adjusts only escaping and formatting required by the programming language;
4. tests assert key phrases and forbidden phrases;
5. master session reviews generated examples, not just code diff.
```

---

## 6. Standing instruction

From now on:

```text
No code agent should be asked to design product wording.
No product wording change is accepted unless the master session supplied the wording or explicitly approved the final exact text.
```
