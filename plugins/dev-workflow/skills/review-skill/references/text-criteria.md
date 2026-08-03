# Text criteria (a–x)

The text pass's full criteria set, loaded by `/review-skill` step 2. **Every criterion is applied to every target; state N/A explicitly rather than silently skipping one** — a pass that quietly covers half its rungs reads exactly like a clean one.

Rate each finding as:
- **SAFE**: No quality risk
- **RISKY**: Could cause the agent to produce lower quality output
- **BROKEN**: Will definitely cause issues — must fix before using
- **NOTE**: An observation for the user to judge, never auto-applied. Reserved for findings that depend on something the file cannot settle — a model default you cannot observe (criterion w), a length trade-off only the author can weigh (criterion x), or the Claude-construct inventory under (s). A NOTE never affects a file's rating and never triggers the auto-fix loop.

## For Agent files (`**/agents/*.md`)

**a. Actionable instructions**
- Was any rule, constraint, or instruction removed (not just reformatted)?
- Were conditional behaviors lost (e.g., "if X then Y" compressed into just "Y")?
- Were mandatory steps removed or made to look optional?

**b. Code examples**
- Are examples still syntactically valid and complete?
- Were important WHY comments removed (comments explaining security, design rationale, or gotchas)?
- Were "bad pattern" examples removed that the agent needs to know what to AVOID?
- Can the agent still use the example as a copy-paste template?

**c. Report format templates**
- Can the agent produce a structured, complete report from the template?
- Were severity levels, sub-fields, or section distinctions lost?
- Were separate sections merged into single lines where the distinction matters (e.g., Critical vs High vs Medium)?

**d. Cross-agent consistency**
- ZERO MISSES directive: still present? Still clear for this agent's role?
- Language line: still unambiguous?
- Mandatory Skills references: still pointing to correct files?

## For Skill files (`**/skills/*/SKILL.md`) and the prose they bundle (`references/*.md`, `templates/*.md`)

**e. Step-by-step workflows**
- Is each step still followable by an agent that has never seen the original?
- Were sub-steps merged in a way that loses sequencing (what comes first)?
- Were decision points preserved (if/else branches, abort conditions)?

**f. Algorithms**
- Were detection/classification algorithms preserved with enough detail to implement?
- Were examples or edge case descriptions removed that the agent needs?

**g. Templates and examples**
- Do output templates still guide the agent to produce complete artifacts?
- Were format examples compressed beyond recognition?

**h. Guardrails and constraints**
- Were any guardrails removed or weakened?
- Were "MUST" / "do NOT" rules softened to suggestions?

**i. Item preservation** (applies to any bullet list, checklist, or enumerated section within the prompt)
- Count bullet items / enumerated entries before and after — were any silently lost in reformatting?
- Were items merged in a way that loses specificity?
- Are section boundaries clear (no two unrelated topics mixed under one heading)?

## Context bloat detection (applies to ALL file types)

**j. Well-known information**
- Does the prompt contain **lengthy explanations** of concepts the model already knows (e.g., multi-paragraph tutorials on what `.value` does, how `computed` works)?
- Only flag as bloat when the content is a **verbose explanation or tutorial** — not when it is a concise rule or constraint. A one-liner like "use `as const` over `enum`" is a rule, not bloat, even if the model knows the concept.
- The test: **"Is this a verbose explanation that adds no actionable constraint, AND would the agent reliably do the right thing without any mention of this topic?"** Both conditions must be true to flag as bloat.
- Principle explanations that merely teach a concept the model already understands should be condensed to a one-line rule. Keep the rule, cut the lecture. **Never remove the rule itself.**

**k. Checklist rules must be grounded in real failures**
- Assume every existing checklist item was added because the agent failed without it. Do NOT remove items just because the model "should know" this.
- Only flag as RISKY (unnecessary) when you can demonstrate with high confidence that the model **never** makes this mistake in the specific context of this agent's role — not in general, but for this agent's actual tasks.
- When evaluating whether to keep or remove a checklist item, the question is: "Is there any plausible scenario where this agent could get this wrong?" If yes, keep it.
- **When k and j conflict** (a verbose rationale that also references a past failure or documents a non-obvious constraint): k wins. Battle-tested content with rationale stays; only the WRITING STYLE may be tightened if bloated. Never remove the rule or its justification.

**l. No assumptions about project tooling**
- Prompts must not assume every project has a linter, formatter, test runner, or CI pipeline configured.
- Rules that depend on optional tooling must be conditional (e.g., "if the project has a linter configured, run it") — not absolute.
- Flag as RISKY if a rule assumes tooling that may not exist.

**m. Redundancy with workflow**
- If a rule is already enforced by an automated workflow, having the same rule in a checklist is only justified when: (1) the checklist is also used outside the workflow, or (2) the workflow enforcement is conditional.
- Pure duplicates that add no value beyond the workflow should be flagged as RISKY (bloat).

**n. Reference file separation**
- If the skill/agent has reference files (e.g., `references/*.md`), check whether the main prompt contains project-specific, platform-specific, or per-entity details that should be split into the corresponding reference file instead of inlined in the main prompt.
- Flag as RISKY if the main prompt contains project-specific details that duplicate or belong in an existing reference file.

**o. Hardcoded values**
- Scan for hardcoded URLs, names, paths, versions, counts, or other literal values embedded directly in the prompt.
- For each hardcoded value, evaluate: **"Could this value differ across projects, environments, or over time?"** If yes, it should be parameterized, derived from context, or made conditional — not baked into the prompt.
- Values that are truly fixed (e.g., a spec name defined by an RFC, a tool's canonical CLI name) are acceptable — but justify why they must be literal.
- Flag as **RISKY** if a value is hardcoded that could reasonably vary. Flag as **BROKEN** if the hardcoded value is already wrong or outdated.

**p. Reference path integrity**
- For every reference path mentioned in the prompt, verify the file actually exists at that path relative to the skill directory.
- Also check that section anchors referenced actually exist in the target file.
- Flag as **BROKEN** if a referenced file does not exist. Flag as **RISKY** if a referenced section heading cannot be found in the target file.

**q. Factual accuracy of named references**
- For every step number, file path, function / method / variable name, or CLI output string **added in the diff**, verify it actually exists:
  - Step N references → check the step count and headings in the current file
  - File paths → use `Glob` to confirm existence
  - Function / method / variable names → grep the codebase
  - CLI output strings → note as "requires manual verification" if cannot confirm programmatically
- Flag as **BROKEN** if a referenced item does not exist. Flag as **RISKY** if the reference is fragile — e.g., a step number without the step name alongside it (breaks on renumbering), or a hardcoded CLI output string that could drift across tool versions.

**r. Cross-file consistency**
- If multiple skills/agents in the same plugin have parallel structures (e.g., reviewer dispatch rules, agent coverage lists, shared prompt templates, repeated guardrails), audit them as a group — not in isolation.
- For each parallel concept, compare corresponding sections across all files. Flag divergences unless there is a documented reason (e.g., one skill explicitly scopes narrower).
- Example: if `skill-A` and `skill-B` both describe reviewer coverage, the lists should match unless one scope is intentionally narrower. A silent divergence is almost always a bug — one file was updated and the other was forgotten.

**s. Claude-first authoring (open standard as the free baseline)**

These prompts target **Claude Code as the authoritative, primary harness** — audit for Claude effectiveness first. The [Agent Skills open standard](https://agentskills.io) (`name` + `description` + plain markdown) is the portable baseline you get for free, but **use Claude-specific features freely wherever they make the prompt work better on Claude — do NOT genericize, water down, or remove them for cross-harness portability.** Other harnesses (Codex, etc.) are handled by a downstream build/compile step that transforms this authoritative source; portability is NOT bought by degrading the source. (Why: Codex doesn't expand `${CLAUDE_*}`, has no `Task`/subagent dispatch, and doesn't bundle agents via plugins — but the answer is to compile for it later, not to cripple the Claude source now.)

**Do NOT flag — this is correct Claude authoring, using these is the whole point:**
- Harness context injection — bang-backtick (a `!` immediately followed by a backtick-wrapped command) in the body.
- Claude tool names in the body — `TodoWrite`, the `Task` / Agent subagent dispatch, `SendMessage`, `AskUserQuestion`.
- `$ARGUMENTS`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, and frontmatter `allowed-tools` / `disallowed-tools` / `argument-hint` / `model:` / `effort:` (on a *dispatched* subagent — see RISKY below for the persona case) / `context: fork` / `disable-model-invocation` / `user-invocable` / `hooks`.
- Subagent / orchestration constructs (`subagent_type`, companion `agents/*.md`, `context: fork` for isolation) — first-class Claude design, not a liability.

(Optional, non-blocking: you MAY emit a one-line NOTE listing which Claude-only constructs a file uses, to inform the future cross-harness compile step — but NEVER rate them RISKY/BROKEN and NEVER auto-rewrite them.)

**BROKEN — Claude *correctness* bugs (not portability), must fix:**
- **Bare relative path in a read/load instruction** — when the body tells the model to read a bundled file by a bare relative path (`references/x.md`, `agents/y.md`), Claude resolves it against the **current working directory (the user's project)**, NOT the skill/plugin dir → it reads the wrong file or nothing. **Fix:** prefix with `${CLAUDE_PLUGIN_ROOT}/` for plugin-level files (a shared `references/` or `agents/` file, or a convention doc at the plugin root) or `${CLAUDE_SKILL_DIR}/` for the skill's OWN bundled files. (Referencing another skill *by name* for the Skill tool is fine bare — that's a name, not a path read.)
- **`name` ≠ parent directory** — the `name:` frontmatter MUST equal the skill's parent folder name exactly (lowercase, hyphens, case-sensitive). A mismatch is a silent load failure. **Fix:** make them match.

**RISKY — flag and fix:**
- **`model:` / `effort:` on a persona-adopted agent** — those keys only take effect when the agent is **dispatched as a subagent** (via the Agent / `Task` tool). When the agent is instead adopted as a persona by the main session — a skill that says "become the X" / "you are now the orchestrator", or a `/role`-style menu — the main session keeps its OWN session model/effort and the frontmatter is never consumed. A hardcoded `effort:` there misleads: it implies a fixed tier that never applies and can contradict the user's actual session effort. **Fix:** drop `model`/`effort` from agents that are only ever adopted as personas; let them inherit the session.
- **Required MCP tool hardcoded by exact name** — a skill that hardcodes `mcp__<server>__<tool>` as a *required* step works only if that exact server is wired under that exact name (true on Claude too). **Fix:** name the capability + the server it needs, and degrade gracefully if absent — don't make an exact MCP tool id a silent hard dependency.

**t. Intra-file contradiction (a changed instruction vs the rest of the same file)**
- When the diff adds or edits a rule, step, or guardrail, check it against the OTHER instructions in the **same file** — do they contradict? (e.g. one step says "MUST NOT do X, ever" while another says "do X as a fallback"; a new default contradicts a stated invariant.) Read the FULL file, not just the diff, so a contradiction with *unchanged* text is visible.
- This is the intra-file analog of (r): (r) compares parallel structures across files; (t) compares sections/steps within one file.
- Flag **BROKEN** if the two instructions cannot both be obeyed (the agent must violate one to follow the other); **RISKY** if reconcilable but ambiguous about which wins. **Fix:** reconcile them — carve the exception into the absolute rule, or state precedence explicitly.
- Scope: this catches contradictions *in the wording*. It does NOT verify that a described procedure actually produces correct behavior when executed (step-ordering that destroys needed state, non-idempotent resume, unhandled crash mid-step) — that is **Lens A** in `logic-lenses.md`, which step 4 of this skill runs.

## Steering effectiveness (applies to ALL file types)

Criteria a–t ask whether the prompt still *says* the right thing. These four ask whether saying it that way actually *changes what the agent does*. A rule the agent would have followed anyway costs load and buys nothing; a rule phrased so the agent can slip past it is worse than no rule. All four judge wording against the model's default behavior, not against a style guide.

**u. Completion criteria — can the agent tell done from not-done?**
- For each step, find the condition that ends it. A step whose bound is vague ("understanding is reached", "the code is reviewed", "sufficient context gathered") lets the agent declare victory early and move on — attention slips to *being done* rather than to the work, and it slips hardest when later steps are visible and beckoning.
- Two properties to check per step: **checkable** (could the agent objectively tell whether it is met?) and, where it matters, **exhaustive** ("every modified file accounted for" bites; "produce a list of files" does not).
- The same demand binds a flat criteria list, not just numbered steps — "every criterion applied, N/A stated explicitly" is what stops an audit from silently covering half its rungs.
- Flag **RISKY** when a step's bound is unfalsifiable. **Fix by sharpening the criterion** — that is additive and safe. Do NOT restructure or split the skill to hide later steps; that is a design change, not a text fix, so surface it as a suggestion for the user instead.

**v. Positive steering over prohibition**
- A prohibition drags the forbidden behavior into context and makes it *more* available, not less: *don't think of an elephant* names the elephant. `never write verbose comments` leaves "verbose comments" as the pattern the agent just read, with a weak modifier in front of it.
- Flag **RISKY** when a rule is phrased purely as a ban and a positive target exists that implies the same constraint (`write one-line comments` for the above).
- **Reconciliation with (h) — h wins on force, v wins on phrasing.** Criterion h forbids *softening* a MUST / do-NOT rule, and this criterion must never be used to do that. The fix is to **add the positive target**, keeping the prohibition's force intact — never to delete a guardrail or downgrade it to a suggestion. Where a behavior genuinely cannot be phrased positively, the bare prohibition stays and is correct; pair it with what to do instead where possible, and leave it alone otherwise.

**w. No-ops — does this line change behavior versus the model's default?**
- A line can be perfectly relevant, perfectly true, and still buy nothing because the model already does it by default. `be thorough` when the agent is already thorough-ish is load spent to say nothing. This is a different test from (j): j asks whether prose is a *verbose explanation*; this asks whether an instruction — however concise — moves the agent at all.
- When a weak instruction is the problem, the fix is usually a **stronger word rather than a different technique** — `relentless` where `be thorough` was a no-op, a concrete named behavior where an adjective was floating. Sharpening is additive; prefer it to removal every time.
- **Report as a NOTE only — never RISKY, never BROKEN, never auto-removed.** Criterion k governs: every existing line is presumed battle-tested, the burden of proof is on removal, and "the model should know this" is exactly the reasoning k exists to refuse. Whether a line is a no-op depends on a model default you cannot observe from the file, so this criterion can suggest and must not act. Deletion is the user's call, made by running the skill without the line — not the auditor's.

**x. Information hierarchy — is each piece at the right depth?**
- A skill's content sits on a ladder: **steps** (in-file, primary — what the agent does, in order), **reference in-file** (definitions and rules consulted on demand), and **reference disclosed** (pushed into a linked file, loaded only when its pointer fires). Push too little down and the steps drown in material; push too much and the agent never sees what it needed.
- **Pointer wording is the reliability lever.** A pointer's *wording*, not its target, decides whether the agent actually reaches the material. A must-have behind a vague pointer ("see the reference for details") is a variance bug — it fires on some runs and not others. Flag **RISKY** and **fix the wording first** (name what is behind it and the condition for reaching it); only pull material back inline if sharpened wording still cannot be trusted. This extends (n), which decides *what* belongs in a reference file; this decides whether the pointer to it works.
- **Length itself is a finding, but disclosure is the cure — not deletion.** A file can be too long even when every line is live, unique, and battle-tested. Where that happens, the fix is to move **reference** behind a well-worded pointer so the steps stay legible, or to split by branch so each path carries only what it needs. **Report as a NOTE**; never resolve length by removing rules, and never at the cost of (k) or the "compression is not always good" guardrail.
