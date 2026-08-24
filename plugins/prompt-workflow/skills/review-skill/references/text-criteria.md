# Text criteria (a–x) — detection and rating

The text pass's criteria, loaded by `/review-skill` step 2 alongside `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md`.

**Division of labour, so no rule lives in two places:** the shared catalogue holds *the rules* — what good looks like and how a violation is visible. This file holds what the catalogue does not: **how to rate a violation, what to auto-fix versus surface, and the criteria that exist only at audit time** (nothing was written wrong; something was lost or is unverifiable). Where a criterion's rule lives in the catalogue, the entry below carries only its letter, its name, its rating policy, and a pointer — deliberately **not** a second copy of the rule.

**Letters are permanent.** Other files cite `criterion t`, `criteria p and q`, `criteria a–x`. Never renumber or drop a letter; retire one by marking it, not by deleting it.

**Every criterion is applied to every target; state N/A explicitly rather than silently skipping one** — a pass that quietly covers half its rungs reads exactly like a clean one.

Rate each finding as:
- **SAFE**: No quality risk
- **RISKY**: Could cause the agent to produce lower quality output
- **BROKEN**: Will definitely cause issues — must fix before using
- **NOTE**: An observation for the user to judge, never auto-applied. Reserved for findings that depend on something the file cannot settle — a model default you cannot observe (criterion w), or a length trade-off only the author can weigh (criterion x), whose frontmatter `description` case is carved back out as **RISKY** because its budget is stated. A NOTE never affects a file's rating and never triggers the auto-fix loop.

## For Agent files (`**/agents/*.md`)

**a. Actionable instructions** — audit-only: this checks what a diff *lost*, which no write-time rule can see.
- Was any rule, constraint, or instruction removed (not just reformatted)?
- Were conditional behaviors lost (e.g., "if X then Y" compressed into just "Y")?
- Were mandatory steps removed or made to look optional?
- **BROKEN** when a mandatory step became optional or a constraint vanished; **RISKY** when a conditional lost its condition. The catalogue's *never delete a rule to tidy up* is the write-time side; this is the detection.

**b. Code examples** — audit-only.
- Are examples still syntactically valid and complete?
- Were important WHY comments removed (comments explaining security, design rationale, or gotchas)?
- Were "bad pattern" examples removed that the agent needs to know what to AVOID?
- Can the agent still use the example as a copy-paste template?

**c. Report format templates** — rule: catalogue *Write it structured* (fixed fields) and *Where content lives* (document formats belong in template files).
- Audit adds: severity levels, sub-fields, and section distinctions must survive a reformat. **BROKEN** if the template can no longer produce a complete report; **RISKY** if a distinction that matters (e.g. Critical vs High vs Medium) was merged into one line.

**d. Cross-agent consistency** — audit-only: these are conventions of the surrounding fleet, invisible from one file.
- ZERO MISSES directive: still present? Still clear for this agent's role?
- Language line: still unambiguous?
- Mandatory Skills references: still pointing to correct files?

## For Skill files (`**/skills/*/SKILL.md`) and the prose they bundle (`references/*.md`, `templates/*.md`)

**e. Step-by-step workflows** — rule: catalogue *Steps: name what each one hands the next*.
- Audit adds: read as someone who has never seen the original. Were sub-steps merged in a way that loses sequencing, or decision points (if/else, abort conditions) dropped? **BROKEN** when a step is no longer followable or a branch lost its condition.

**f. Algorithms** — audit-only.
- Were detection/classification algorithms preserved with enough detail to implement?
- Were examples or edge case descriptions removed that the agent needs?

**g. Templates and examples** — rule: catalogue *Where content lives* (template files) and *Rules first, examples second*.
- Audit adds: **RISKY** when an output template no longer guides the agent to a complete artifact, or a format example was compressed beyond recognition.

**h. Guardrails and constraints** — rule: catalogue *Never delete a rule to tidy up*.
- Audit adds the softening check, which is not deletion and so reads clean in a diff: a "MUST" or "do NOT" downgraded to a suggestion is **BROKEN**, not a wording preference. **This criterion outranks (v)** — never soften a prohibition to satisfy phrasing.

**i. Item preservation** (any bullet list, checklist, or enumerated section) — rule: catalogue *Never delete a rule to tidy up* (count items before and after).
- Audit adds: count the entries on both sides of the diff and reconcile. Were items merged in a way that loses specificity? Are section boundaries still clean (no two unrelated topics under one heading)? **BROKEN** on a silent loss, **RISKY** on a lossy merge.

## Context bloat detection (applies to ALL file types)

**j. Well-known information** — rule: catalogue *Cost*, step 4 (cut the lecture, never the rule).
- Audit adds the two-part test, and both halves must hold before flagging: **"Is this a verbose explanation that adds no actionable constraint, AND would the agent reliably do the right thing without any mention of this topic?"** A one-liner is a rule, not bloat, however obvious the concept. Flag **RISKY** and condense to a one-line rule; never remove the rule itself.

**k. Checklist rules must be grounded in real failures** — this is a **policy about the burden of proof**, and it governs the whole pass.
- Assume every existing checklist item was added because the agent failed without it. Do NOT remove items just because the model "should know" this.
- Only flag as RISKY (unnecessary) when you can demonstrate with high confidence that the model **never** makes this mistake in the specific context of this agent's role — not in general, but for this agent's actual tasks.
- The question is: "Is there any plausible scenario where this agent could get this wrong?" If yes, keep it.
- **When k and j conflict** (a verbose rationale that also references a past failure or documents a non-obvious constraint): **k wins.** Battle-tested content with rationale stays; only the WRITING STYLE may be tightened. Never remove the rule or its justification.

**l. No assumptions about project tooling** — rule: catalogue *Depending on anything outside the file* (absence plan).
- Audit adds: a rule that depends on optional tooling must read as conditional. **RISKY** when it assumes a linter, formatter, test runner, or CI that may not exist.

**m. Redundancy with workflow** — rule: catalogue *One canonical home per rule*.
- Audit adds the exemptions: a rule duplicated from an automated workflow is justified when (1) the checklist is also used outside that workflow, or (2) the workflow's enforcement is conditional. Otherwise **RISKY** (bloat).

**n. Reference file separation** — rule: catalogue *Where content lives*.
- Audit adds: **RISKY** when the main prompt inlines project-specific, platform-specific, or per-entity detail that duplicates — or belongs in — an existing reference file.

**o. Hardcoded values** — audit-only for the general literal (only a reader outside the file can tell whether a project name or a path will vary). Two kinds now have a write-time rule in the catalogue and this criterion supplies their rating: a fact that lives in another system — a version, a CLI flag, an API or payload shape — is *A fact that rots somewhere else is cited, not copied in*; a literal that scripts a route through the target — a line range, a file list, a count — is *Be exact about the destination, never the route*.
- Scan for hardcoded URLs, names, paths, versions, counts, or other literals.
- For each: **"Could this value differ across projects, environments, or over time?"** If yes, parameterize, derive, or conditionalize it.
- Truly fixed values (an RFC-defined name, a tool's canonical CLI name) are acceptable — but justify why they must be literal.
- **RISKY** if a value could reasonably vary; **BROKEN** if it is already wrong or outdated.

**p. Reference path integrity** — audit-only: existence can only be checked against the filesystem.
- For every reference path in the prompt, verify the file exists at that path relative to the skill directory.
- Check that referenced section anchors exist in the target file.
- **BROKEN** if a referenced file does not exist; **RISKY** if a referenced heading cannot be found.

**q. Factual accuracy of named references** — audit-only: verification, not authoring.
- For every step number, file path, function / method / variable name, or CLI output string **added in the diff**, verify it exists:
  - Step N references → check the step count and headings in the current file
  - File paths → use `Glob` to confirm existence
  - Function / method / variable names → grep the codebase
  - CLI output strings → note as "requires manual verification" if not confirmable programmatically
- **A target whose content rots without being edited is verified whole, not diff-scoped** — e.g. a `CLAUDE.md`, or any prose naming build/test commands, codebase paths, or a tech-stack version. Those lines go stale because the *codebase* moved, with nobody touching the file, so the "added in the diff" filter above passes a command that no longer runs. Verify every command and path such a file names, changed or not.
- **BROKEN** if a referenced item does not exist. **RISKY** if the reference is fragile — a step number without its name (the catalogue's rule), or a hardcoded CLI string that drifts across tool versions.

**r. Cross-file consistency** — rule: catalogue *Before changing a rule, grep a distinctive token from it*.
- Audit adds: audit parallel structures across the plugin as a **group**, not in isolation — reviewer dispatch rules, agent coverage lists, shared templates, repeated guardrails. Flag divergence unless one file explicitly scopes narrower. A silent divergence is almost always a bug: one file was updated and the other forgotten.

**s. Claude-first authoring (open standard as the free baseline)** — audit-only **policy**: what NOT to flag.

These prompts target **Claude Code as the authoritative, primary harness** — audit for Claude effectiveness first. The [Agent Skills open standard](https://agentskills.io) (`name` + `description` + plain markdown) is the portable baseline you get for free, but **use Claude-specific features freely wherever they make the prompt work better on Claude — do NOT genericize, water down, or remove them for cross-harness portability.** Other harnesses (Codex, etc.) are handled by a downstream build/compile step that transforms this authoritative source; portability is NOT bought by degrading the source. (Why: Codex doesn't expand `${CLAUDE_*}`, has no `Task`/subagent dispatch, and doesn't bundle agents via plugins — but the answer is to compile for it later, not to cripple the Claude source now.)

**Do NOT flag — this is correct Claude authoring, using these is the whole point:**
- Harness context injection — bang-backtick (a `!` immediately followed by a backtick-wrapped command) in the body.
- Claude tool names in the body — `TodoWrite`, the `Task` / Agent subagent dispatch, `SendMessage`, `AskUserQuestion`.
- `$ARGUMENTS`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, and frontmatter `allowed-tools` / `disallowed-tools` / `argument-hint` / `model:` / `effort:` (on a *dispatched* subagent — see RISKY below for the persona case) / `context: fork` / `disable-model-invocation` / `user-invocable` / `hooks`.
- Subagent / orchestration constructs (`subagent_type`, companion `agents/*.md`, `context: fork` for isolation) — first-class Claude design, not a liability.

**BROKEN — Claude *correctness* bugs (not portability), must fix.** Both rules live in the catalogue's *Names and paths that resolve*; the ratings are here:
- **Bare relative path in a read/load instruction** → **BROKEN**. Fix per the catalogue: `${CLAUDE_PLUGIN_ROOT}/` for plugin-level files, `${CLAUDE_SKILL_DIR}/` for the skill's own. (Referencing another skill *by name* for the Skill tool is fine bare — that's a name, not a path read.)
- **`name` ≠ parent directory** → **BROKEN**, a silent load failure. Fix: make them match.

**RISKY — flag and fix:**
- **`model:` / `effort:` on a persona-adopted agent** — those keys only take effect when the agent is **dispatched as a subagent** (via the Agent / `Task` tool). When the agent is instead adopted as a persona by the main session — a skill that says "become the X" / "you are now the orchestrator", or a `/role`-style menu — the main session keeps its OWN model/effort and the frontmatter is never consumed. A hardcoded `effort:` there implies a tier that never applies and can contradict the user's actual session effort. **Fix:** drop `model`/`effort` from agents only ever adopted as personas. **Do NOT flag** an agent that is *also* dispatched as a subagent — there the keys are live, and the persona path is handled correctly by whichever skill adopts it declining to read them.
- **Required MCP tool hardcoded by exact name** — a skill that hardcodes `mcp__<server>__<tool>` as a *required* step works only if that exact server is wired under that exact name. **Fix:** name the capability plus the server it needs, and degrade per the catalogue's absence-plan rule — never a silent hard dependency.

**t. Intra-file contradiction (a changed instruction vs the rest of the same file)** — audit-only: only a full re-read surfaces it.
- When the diff adds or edits a rule, step, or guardrail, check it against the OTHER instructions in the **same file** — do they contradict? (e.g. one step says "MUST NOT do X, ever" while another says "do X as a fallback"; a new default contradicts a stated invariant.) Read the FULL file, not just the diff, so a contradiction with *unchanged* text is visible.
- This is the intra-file analog of (r): (r) compares parallel structures across files; (t) compares sections/steps within one file.
- **BROKEN** if the two instructions cannot both be obeyed (the agent must violate one to follow the other); **RISKY** if reconcilable but ambiguous about which wins. **Fix:** reconcile — carve the exception into the absolute rule, or state precedence explicitly.
- Scope: wording only. Whether the described procedure actually *behaves* correctly is **Lens A** in `logic-lenses.md`.

## Steering effectiveness (applies to ALL file types)

Criteria a–t ask whether the prompt still *says* the right thing. These four ask whether saying it that way actually *changes what the agent does*. All four judge wording against the model's default behavior, not against a style guide.

**u. Completion criteria — can the agent tell done from not-done?** — rule: catalogue *Done-conditions must be checkable*.
- Audit adds the two properties to test per step: **checkable** (could the agent objectively tell whether it is met?) and, where it matters, **exhaustive**. The same demand binds a flat criteria list, not just numbered steps — "every criterion applied, N/A stated explicitly" is what stops a pass covering half its rungs. **RISKY** when a bound is unfalsifiable; fix by sharpening the criterion, which is additive and safe. Do NOT restructure or split the skill to hide later steps — that is a design change, so surface it as a suggestion instead.

**v. Positive steering over prohibition** — rule: catalogue *Give a positive target alongside a prohibition*.
- Audit adds: **RISKY** when a rule is phrased purely as a ban and a positive target exists that implies the same constraint. **Reconciliation with (h): h wins on force, v wins on phrasing.** The fix is to **add** the positive target, keeping the prohibition intact — never to delete a guardrail or downgrade it. Where a behavior genuinely cannot be phrased positively, the bare prohibition stays and is correct.

**w. No-ops — does this line change behavior versus the model's default?** — audit-only, and **NOTE only**.
- A line can be relevant, true, and still buy nothing because the model already does it by default. This differs from (j): j asks whether prose is a *verbose explanation*; this asks whether an instruction — however concise — moves the agent at all.
- When a weak instruction is the problem, the fix is usually a **stronger word rather than a different technique**. Sharpening is additive; prefer it to removal every time.
- **Report as a NOTE only — never RISKY, never BROKEN, never auto-removed.** Criterion k governs: the burden of proof is on removal, and "the model should know this" is exactly the reasoning k refuses. Whether a line is a no-op depends on a model default you cannot observe from the file, so this criterion may suggest and must not act. Deletion is the user's call.

**x. Information hierarchy — is each piece at the right depth?** — rule: catalogue *Where content lives* (the extract/don't-extract tests and pointer wording).
- Audit adds three ratings. A must-have behind a vague pointer is a **variance bug**: **RISKY**, and fix the wording first (name what is behind it and the condition for reaching it); only pull material back inline if sharpened wording still cannot be trusted. And **length itself is a finding, but disclosure is the cure — not deletion**: a file can be too long even when every line is live, unique, and battle-tested. **Report length as a NOTE**; never resolve it by removing rules, and never at the cost of (k). **The frontmatter `description` is carved out of that NOTE**: a body's length is a trade-off only the author can weigh, while a description's budget and the way to meet it are both stated — the catalogue's *Compress every description by default* — so an over-budget description is **RISKY** and fixed in the pass, under that entry's before/after list, which is what stops the trim narrowing what reaches the skill. The situations it checked go in that fix's `### 已修` entry; an unreported list is an unrun one.
