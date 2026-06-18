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

   If files are specified, use them. Otherwise:
   - Run `git diff --name-only` to find modified files
   - Filter to paths matching `**/agents/*.md` or `**/skills/*/SKILL.md` (match by path suffix; ignore any leading directories like `plugins/<name>/`)
   - If no relevant changes found, report and stop

2. **For each file, read the FULL current version and the diff**

   - Read the complete file (not just the diff — context matters)
   - Run `git diff HEAD -- <file>` to see what changed (or `git diff HEAD~1` if already committed)

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

   **s. Cross-harness portability (Agent Skills open standard)**

   Skills and agents here target the [Agent Skills open standard](https://agentskills.io) (SKILL.md), now supported by a broad and growing set of harnesses (Claude Code, Codex, Cursor, GitHub Copilot, Gemini, and many more). **Audit against the standard, not against each tool** — do NOT maintain a per-tool matrix; the harness list churns constantly. The single rule of thumb: **"`name` + `description` + plain markdown works everywhere; everything else is an extension that a harness without support for it silently ignores."** Do NOT blanket-remove harness extensions: ignored ≠ broken, and removing them loses value on the harness that does support them for zero portability gain. Claude Code and Codex below are concrete worked examples of the two failure shapes — the same classification covers every standard-compliant harness.

   **BROKEN — must fix (silently does the WRONG thing on the other harness, and has a portable equivalent):**
   - **Harness context injection** — `` !`cmd` `` in the body expands only in Claude Code; on Codex it stays literal and the agent acts on empty/wrong context. **Fix:** replace with an explicit instruction to run the same command first and use its output (e.g. "Run `git diff --name-only` and use the result"). Identical behavior on Claude Code.
   - **`name` ≠ parent directory** — the `name:` frontmatter MUST equal the skill's parent folder name exactly (lowercase, hyphens, case-sensitive). A mismatch is a *silent* load failure on some harnesses. **Fix:** make them match.

   **RISKY — flag and fix the wording (degrades, but can mislead a literal agent):**
   - **Hardcoded harness tool names in the body** — Codex follows instructions very literally: telling it to "use your `TodoWrite` tool" / "use the `Task` tool" makes it hunt for a tool by that exact name that does not exist on Codex (Claude's `TodoWrite` ≈ Codex `update_plan`; Claude's `Task`/subagents have no Codex equivalent). **Fix:** refer to the *capability* generically — "track your steps in a task list", "search the codebase", "read the file" — not the Claude tool name. **Exception:** skills whose subject IS Claude Code tooling, where the tool name is the actual content (keep, it's intentional).
   - **`$ARGUMENTS` in the body** — Claude Code substitutes it in place; on Codex in-place substitution is a custom-prompt feature not guaranteed for skills, so it may stay literal (the model still reads it as a placeholder and infers intent from the user's actual message). Keeping it is net positive — full function on Claude Code, harmless literal on Codex. Flag RISKY **only if the logic requires exact in-place substitution**; fix by wording it so the skill also works when args arrive as free text. Do NOT remove `$ARGUMENTS`.
   - **Required MCP tool, hardcoded by exact name** — a skill that hardcodes `mcp__<server>__<tool>` as a *required* step works only if the user wired that exact MCP server under that exact name. **Fix:** name the capability and the server it needs, and degrade gracefully if absent — don't make an exact MCP tool id a silent hard dependency.

   **SAFE — keep as-is (silently ignored by harnesses that don't support it; gracefully degrades):**
   - Frontmatter `allowed-tools`, `disallowed-tools`, `argument-hint`, `model:`, `effort:`, `context: fork`, `disable-model-invocation`, `user-invocable`, `hooks` — enforced on Claude Code, ignored on Codex. Keep them; they cost nothing on the harness that ignores them.

   **SAFE but NOTE — never auto-rewrite (intentional, documented design choice):**
   - Subagent / orchestration constructs: `subagent_type`, Task/Agent dispatch, companion `agents/*.md`, and `context: fork` relied on for isolation. Codex has no equivalent; the skill degrades to running inline in the main agent. This is an architectural decision tracked in the README compatibility table — emit a one-line portability note in the report, but do NOT rewrite the architecture and do NOT rate it BROKEN/RISKY.

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
- **Portable across harnesses, but don't strip graceful features** — `name`+`description`+plain markdown is the portable core. FIX: `` !`cmd` `` injection (→ explicit "run the command"), `name`≠directory, body text that names Claude-only tools like `TodoWrite`/`Task` (→ name the capability, not the tool). KEEP (harmlessly ignored on Codex): `allowed-tools` / `model:` / `argument-hint` / `hooks` / `context: fork`. NEVER auto-rewrite subagent dispatch — intentional Claude-first design, note it and move on
- **Prefer generic over hardcoded** — prompts should work across projects. Hardcoded values (URLs, names, paths, versions) need justification; if a value could vary, parameterize or conditionalize it
- **Zero errors is the absolute principle** — when in doubt, rate as RISKY and fix it
- **Auto-fix, don't ask** — fix BROKEN/RISKY issues immediately, re-audit, repeat until clean
