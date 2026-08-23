# Reviewer Analytical Depth

The **Analytical depth requirement** every reviewer dispatch must carry. Single source for `/apply` (Phase 2 initial run AND every fresh-review retry round), `/quick` (all complexity tiers), and `/review` (every lens dispatch, one copy per agent when the scope is sharded).

**Who gets it:** `review-engineer`, `security-engineer`, `qa-engineer`.

**Who must NOT get it:** every implementation and fix agent (Backend / Frontend / Python / Godot / Electron / Database / DevOps / **Performance**), and the Phase 3 `technical-writer`. They are executors — category enumeration there produces over-engineered code and padded docs. This exclusion is the reason the block lives here rather than in `agent-guidelines` (which every agent loads eagerly).

`performance-engineer` stays excluded even when dispatched as a reviewer in its own right (Phase 2's conditional 4th reviewer, or `/review`'s `performance` lens): its own agent file already prescribes a per-data-path verdict table (anchor / growth driver / verdict / degrade threshold), which is its coverage discipline. Layering this block on top would duplicate that structure rather than enforce it.

**Rationale:** structurally enforcing exhaustive scanning and auditable coverage is the primary safeguard — a reviewer that reports only what caught its eye has silently chosen its own scope.

**A returned report that violates these requirements gets bounced, not papered over.** Severity is what decides whether the run stops, and silence on a category is defined below as a skipped category — so a finding with no severity, or a category the report never mentions, leaves a verdict that cannot be acted on. Send it back to the same agent with `SendMessage` naming the missing part; its context is intact, so this is far cheaper than a re-dispatch, and cheaper than assigning the severity yourself — a dispatcher-invented severity is a guess wearing the reviewer's judgement. Observed: a security report returned one finding with no severity and the round was accepted anyway.

---

Include the following verbatim in each reviewer's dispatched prompt:

> **Analytical depth requirement**
>
> **Before reading anything, take the project's review criteria if there are any.** If a `review-criteria` skill is available to you, load it with the Skill tool now. If none resolves, skip it — this block and your own report format stand on their own — and say so in one line, so a run with the criteria is distinguishable from a run without them.
>
> **When they load, they outrank this block and your own report format.** Reading depth, the bar an item must clear to be written down, the shapes items take, the section layout, and the counting lines are all theirs, rendered as they specify — do not reshape their output into your usual format. This block then supplies only what they leave open — the numbered requirements below.
>
> Two things they do not reach, because they never claimed them. **Your dispatched scope** — which files are yours, and your own shard when the review was sharded — was settled by whoever dispatched you; their depth rules choose how deeply to read *within* that set, never which set it is. And **their duplicate-merging covers your own findings only**; merging across reviewers happens after you, so never reach for another reviewer's items.
>
> **Report in Traditional Chinese**, leaving code, identifiers and quoted snippets verbatim. That is this workflow's language, and it settles the language of whatever headings and labels the criteria's own layout asks for.
>
> 1. **Enumerate coverage BEFORE findings** — list the categories/dimensions you examined:
>    - `review-engineer` → architecture compliance, correctness, performance, readability, test quality, change history & in-code constraints
>    - `security-engineer` → each applicable OWASP Top-10 category, authN/authZ, input validation, secrets/config, dependency risks
>    - `qa-engineer` → every acceptance scenario, plus happy path + edge cases + error paths + authorization cases. Scenarios come from the spec's WHEN/THEN clauses when the target has one (`/apply`, and `/review` when its e2e gate found a covering spec); from the acceptance criteria the user supplied when it has no spec but they gave one (`/review`'s ad-hoc path); otherwise enumerate every affected user-facing flow (`/quick`, and `/review`'s smoke-only path — which is labelled NOT acceptance and states that in its report).
> 2. **Confirm non-findings explicitly** — for every category examined, state the result. "No issues found in category X" is a valid and expected outcome. Silence on a category is treated as "agent skipped it" and fails the review.
> 3. **Severity-rank every finding** — `blocker` / `major` / `minor`, each with a one-line rationale. Raw observations without severity are rejected.
