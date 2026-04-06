---
name: review-prompt
description: Use when auditing or reviewing agent and skill prompt files for quality, or when the user asks to review prompts or run /review-prompt.
---

# Prompt Audit

Audit agent and skill prompt files for quality risks. **Zero errors > speed > brevity.**

---

**Input**: Optionally specify files via `$ARGUMENTS`. If omitted, auto-detect changed files via `git diff`. Pass `--report-only` in `$ARGUMENTS` to stop after the report without auto-fixing.

**Steps**

1. **Identify files to audit**

   **Scope**: This skill assumes Claude Code plugin structure — agent files matching `**/agents/*.md` and skill files matching `**/skills/*/SKILL.md` at any depth (e.g. `plugins/<name>/skills/<skill>/SKILL.md`). For non-plugin projects, specify target files explicitly via `$ARGUMENTS`.

   If files are specified, use them. Otherwise auto-detect:
   - Run `git diff --name-only` (uncommitted changes).
   - **If the working tree is clean**, fall back to the most recent commit batch instead of stopping — this is the common case when `/review-prompt` runs right after `/commit`. Inspect `git log --oneline`, pick the run of related commits just made, and use `git diff --name-only <base>..HEAD` (default `HEAD~1..HEAD` if a single commit; widen to `HEAD~N..HEAD` to cover a multi-commit batch). Record that range — step 2 reuses it.
   - Filter to paths matching `**/agents/*.md` or `**/skills/*/SKILL.md` (match by path suffix; ignore any leading directories like `plugins/<name>/`)
   - Only if neither uncommitted changes NOR the recent commit batch touch any in-scope file, report and stop

2. **For each file, read the FULL current version and the diff**

   - Read the complete file (not just the diff — context matters)
   - Run `git diff HEAD -- <file>` for uncommitted changes, or `git diff <base>..HEAD -- <file>` using the range recorded in step 1 when the changes are already committed (do NOT use bare `HEAD~1` for a multi-commit batch — it misses all but the last commit)

3. **Audit every change against these criteria**

   Rate each finding as:
   - **SAFE**: No quality risk
   - **RISKY**: Could cause the agent to produce lower quality output
   - **BROKEN**: Will definitely cause issues — must fix before using

   ### For Agent files (`**/agents/*.md`)

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

   ### For Skill files (`**/skills/*/SKILL.md`)

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

   ### Context bloat detection (applies to ALL file types)

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
   - **Bare relative path in a read/load instruction** — when the body tells the model to read a bundled file by a bare relative path (`references/x.md`, `agents/y.md`), Claude resolves it against the **current working directory (the user's project)**, NOT the skill/plugin dir → it reads the wrong file or nothing. **Fix:** prefix with `${CLAUDE_PLUGIN_ROOT}/` for plugin-level files (shared `references/`, `agents/`, `company-conventions.md`) or `${CLAUDE_SKILL_DIR}/` for the skill's OWN bundled files. (Referencing another skill *by name* for the Skill tool is fine bare — that's a name, not a path read.)
   - **`name` ≠ parent directory** — the `name:` frontmatter MUST equal the skill's parent folder name exactly (lowercase, hyphens, case-sensitive). A mismatch is a silent load failure. **Fix:** make them match.

   **RISKY — flag and fix:**
   - **`model:` / `effort:` on a persona-adopted agent** — those keys only take effect when the agent is **dispatched as a subagent** (via the Agent / `Task` tool). When the agent is instead adopted as a persona by the main session — a skill that says "become the X" / "you are now the orchestrator", or a `/role`-style menu — the main session keeps its OWN session model/effort and the frontmatter is never consumed. A hardcoded `effort:` there misleads: it implies a fixed tier that never applies and can contradict the user's actual session effort. **Fix:** drop `model`/`effort` from agents that are only ever adopted as personas; let them inherit the session.
   - **Required MCP tool hardcoded by exact name** — a skill that hardcodes `mcp__<server>__<tool>` as a *required* step works only if that exact server is wired under that exact name (true on Claude too). **Fix:** name the capability + the server it needs, and degrade gracefully if absent — don't make an exact MCP tool id a silent hard dependency.

   **t. Intra-file contradiction (a changed instruction vs the rest of the same file)**
   - When the diff adds or edits a rule, step, or guardrail, check it against the OTHER instructions in the **same file** — do they contradict? (e.g. one step says "MUST NOT do X, ever" while another says "do X as a fallback"; a new default contradicts a stated invariant.) Read the FULL file, not just the diff, so a contradiction with *unchanged* text is visible.
   - This is the intra-file analog of (r): (r) compares parallel structures across files; (t) compares sections/steps within one file.
   - Flag **BROKEN** if the two instructions cannot both be obeyed (the agent must violate one to follow the other); **RISKY** if reconcilable but ambiguous about which wins. **Fix:** reconcile them — carve the exception into the absolute rule, or state precedence explicitly.
   - Scope: this catches contradictions *in the wording*. It does NOT verify that a described procedure actually produces correct behavior when executed (step-ordering that destroys needed state, non-idempotent resume, unhandled crash mid-step) — that is a separate logic audit, `/review-workflow`, out of scope here.

4. **Produce the audit report**

   **Language**: Audit report MUST be written in Traditional Chinese. Technical terms (file names, code, rating labels like SAFE/RISKY/BROKEN) remain in English.

   **Finding format is MANDATORY structured** — every finding MUST include: location (`file:line`), what changed, and risk/failure/rationale. Bare `[description]` is not acceptable output.

   ```
   ## Prompt Audit Report

   ### Files Audited: N

   ### [filename]
   **Rating: [SAFE / RISKY / BROKEN]**

   #### SAFE changes
   - [file:line] [what changed] — [one-line why safe]

   #### RISKY findings
   - [file:line] [what changed] — risk: [what could go wrong] — suggested fix: [concrete action]

   #### BROKEN findings
   - [file:line] [what changed] — will cause: [specific failure] — required fix: [concrete action]

   ### Summary
   | File | Rating |
   |------|--------|
   | ... | SAFE / RISKY / BROKEN |

   **Verdict: [ALL SAFE / HAS RISKS / HAS BROKEN]**
   ```

5. **Auto-fix until ALL SAFE**

   If `--report-only` was passed in `$ARGUMENTS`, STOP after the Step 4 report — do not modify any files.

   Otherwise, if any BROKEN or RISKY findings exist:
   a. Fix them immediately — do NOT ask the user, just fix.
   b. After fixing, re-run the full audit (Step 2-4) on the fixed files.
   c. Repeat until all files are rated **SAFE**.
   d. Max 3 rounds — if still not all SAFE after 3 rounds, report remaining issues and stop.

   Show the user only the final result:
   ```
   ## Prompt Audit: ALL SAFE
   Files audited: N | Rounds: M
   [one-line summary per file]
   ```

   If stopped after 3 rounds:
   ```
   ## Prompt Audit: N issues remaining after 3 rounds
   [list remaining RISKY/BROKEN with details]
   ```

---

## Guardrails

- **Read the FULL file, not just the diff** — context determines whether a change is safe
- **Be strict** — flag anything even slightly questionable as RISKY
- **Never approve removal of**: ZERO MISSES directives, mandatory phase instructions, security-related comments, severity-level distinctions in reports, engineering-checklist principles, project-specific conventions that the model cannot infer on its own
- **Compression is not always good** — shorter prompts that lose clarity are worse than longer prompts that work correctly
- **Bloat is also a risk** — but ONLY for verbose explanations and tutorials, not for concise rules or constraints
- **Presume existing content is battle-tested** — every rule in the prompt was likely added because the agent failed without it. The burden of proof is on removal.
- **No tooling assumptions** — rules must not assume linter, formatter, test runner, or CI are always present
- **Claude-first; defer cross-harness to a compile step** — Claude Code is the authoritative target. Use Claude features freely (bang-backtick, `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_SKILL_DIR}`, `TodoWrite`/`Task`/subagent dispatch, `$ARGUMENTS`, `hooks`, `model:`/`effort:`); do NOT degrade them for portability — a downstream build step transforms the source for other harnesses. The only Claude-*correctness* fixes here: a read/load instruction with a bare relative path to a bundled file (→ prefix `${CLAUDE_PLUGIN_ROOT}/` or `${CLAUDE_SKILL_DIR}/`), `name` ≠ parent directory, and `model:`/`effort:` on a persona-adopted agent (→ remove; it inherits the session)
- **Prefer generic over hardcoded** — prompts should work across projects. Hardcoded values (URLs, names, paths, versions) need justification; if a value could vary, parameterize or conditionalize it
- **Zero errors is the absolute principle** — when in doubt, rate as RISKY and fix it
- **Auto-fix, don't ask** — fix BROKEN/RISKY issues immediately, re-audit, repeat until clean
