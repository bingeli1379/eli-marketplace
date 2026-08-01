# Reviewer Analytical Depth

The **Analytical depth requirement** every reviewer dispatch must carry. Single source for `/apply` (Phase 2 initial run AND every fresh-review retry round) and `/quick` (all complexity tiers).

**Who gets it:** `review-engineer`, `security-engineer`, `qa-engineer`.

**Who must NOT get it:** every implementation and fix agent (Backend / Frontend / Python / Godot / Electron / Database / DevOps / **Performance**), and the Phase 3 `technical-writer`. They are executors — category enumeration there produces over-engineered code and padded docs. This exclusion is the reason the block lives here rather than in `agent-guidelines` (which every agent loads eagerly).

`performance-engineer` stays excluded even when dispatched as Phase 2's conditional 4th reviewer: its own agent file already prescribes a per-data-path verdict table (anchor / growth driver / verdict / degrade threshold), which is its coverage discipline. Layering this block on top would duplicate that structure rather than enforce it.

**Rationale:** structurally enforcing exhaustive scanning and auditable coverage is the primary safeguard — a reviewer that reports only what caught its eye has silently chosen its own scope.

---

Include the following verbatim in each reviewer's dispatched prompt:

> **Analytical depth requirement**
>
> 1. **Enumerate coverage BEFORE findings** — list the categories/dimensions you examined:
>    - `review-engineer` → architecture compliance, correctness, performance, readability, test quality
>    - `security-engineer` → each applicable OWASP Top-10 category, authN/authZ, input validation, secrets/config, dependency risks
>    - `qa-engineer` → every acceptance scenario, plus happy path + edge cases + error paths + authorization cases. Scenarios come from the spec WHEN/THEN clauses when the change has specs (`/apply`); when it has none (`/quick`), enumerate every affected user-facing flow instead.
> 2. **Confirm non-findings explicitly** — for every category examined, state the result. "No issues found in category X" is a valid and expected outcome. Silence on a category is treated as "agent skipped it" and fails the review.
> 3. **Severity-rank every finding** — `blocker` / `major` / `minor`, each with a one-line rationale. Raw observations without severity are rejected.
