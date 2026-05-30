---
name: validate
description: >
  Validate spec artifacts against structural and content rules.
  Use when the user wants to check if spec artifacts are complete and well-formed
  before implementation.
user-invocable: true
---

Validate spec artifacts for a change. Checks structural completeness, content quality, and referential integrity. All violations are errors — any failure blocks implementation.

---

**Input**: The argument is a change name (e.g., `/validate add-user-search`).

**Steps**

1. **Parse input**

   Extract `<change-name>` from the argument.

   If no change name provided:
   - List directories under `feature-spec/changes/` (excluding `archive/`)
   - If only one active change exists, auto-select it
   - If multiple, use **AskUserQuestion** to let the user choose
   - If none exist, report error: "No active changes found. Run `/propose` first."

2. **Verify change directory exists**

   Check that `feature-spec/changes/<name>/` exists. If not, report error with available changes.

3. **Run validation checks**

   Read all artifact files and validate against the rules below. Collect ALL issues before reporting.

4. **Generate report**

   Display the validation report (see Output Format below).

---

## Validation Rules

Most rules are **ERROR** level — any ERROR causes FAIL. A few rules are marked **WARN** (e.g. mixed agent types in a group, missing `Reference:` line): they surface a quality risk but do **not** block implementation. Report both, but only ERRORs flip the verdict to FAIL.

### File Existence

| Check | Rule |
|-------|------|
| `proposal.md` | MUST exist |
| `design.md` | MUST exist |
| `tasks.md` | MUST exist |
| `specs/` directory | MUST exist and contain at least one `<capability>/spec.md` |

### proposal.md

| Check | Rule |
|-------|------|
| `## Why` section | MUST exist and be non-empty (at least 50 characters) |
| `## What Changes` section | MUST exist and be non-empty |
| `## Capabilities` section | MUST exist |
| `### New Capabilities` or `### Modified Capabilities` | At least one MUST list capabilities |
| `## Impact` section | MUST exist and be non-empty |
| Capability naming | Each capability name MUST be kebab-case |
| Capability descriptions | Each capability MUST have a description after the name |

### design.md

| Check | Rule |
|-------|------|
| `## Context` section | MUST exist and be non-empty |
| `## Goals / Non-Goals` section | MUST exist |
| `**Goals:**` list | MUST exist and contain at least one item |
| `**Non-Goals:**` list | MUST exist and contain at least one item |
| `## Domain Model (DDD)` section | MUST exist when Backend impact is indicated in proposal |
| `## API Contract` section | MUST exist when both Backend and Frontend are impacted |
| `## Shared Types` section | MUST exist when both Backend and Frontend are impacted |
| `## Decisions` section | MUST exist with at least one decision |
| Decision alternatives | Each decision MUST mention at least one alternative considered |
| `## Risks / Trade-offs` section | MUST exist and be non-empty |

### tasks.md

| Check | Rule |
|-------|------|
| Numbered groups | MUST have at least one `## N. [Group]` heading |
| Checkbox format | All tasks MUST use `- [ ]` or `- [x]` checkbox format |
| Single agent type per group | Each group SHOULD contain only one agent-type tag. WARN if a group mixes multiple agent types (e.g., both `(Backend)` and `(Frontend)` tasks in the same group). Mixed groups produce mixed-concern commits after squash. |
| Group heading descriptiveness | Group heading MUST NOT be just an agent type name (e.g., `Backend`, `Frontend`, `E2E`). It must describe the reviewable concern (e.g., `Search API and service layer`). |
| Dependency annotation format | If `<!-- depends: N[, M...] -->` is present on a heading, referenced group numbers MUST exist in tasks.md |
| Shared file conflict | If `design.md` has an Affected Files section, two independent groups (no dependency between them) MUST NOT both list the same file. ERROR — must add a dependency or merge the groups. This is a backstop only: it catches collisions only when files are enumerated per group. Catch-all wording ("rewrite all N consumers") hides the real paths, so the primary collision check is propose's Step 9a self-review (grep the inventory). Do NOT assume this rule covers refactors. |
| Task numbering | Tasks MUST use `N.M` numbering (e.g., `1.1`, `1.2`, `2.1`) |
| Task verb | Each task description MUST start with a verb (e.g., Create, Implement, Add, Write, Configure) |
| Empty groups | Groups MUST NOT be empty (no tasks under heading) |
| Reference pointer | Each group SHOULD carry a `Reference:` line (the nearest existing analog to mirror, or `Reference: none`). WARN if missing — the implementing and reviewing agents lose their pattern anchor and the change risks style drift. |
| Repo annotation (multi-repo) | If a group heading carries a `<!-- repo: <path> -->` annotation, `<path>` MUST resolve to a directory on disk. ERROR if it does not. |

### specs/\*/spec.md

| Check | Rule |
|-------|------|
| `### Requirement:` heading | Each spec MUST have at least one Requirement |
| SHALL/MUST keyword | Each Requirement text MUST contain `SHALL` or `MUST` |
| `#### Scenario:` blocks | Each Requirement MUST have at least one Scenario |
| WHEN/THEN format | Each Scenario MUST contain `**WHEN**` and `**THEN**` lines |
| Requirement length | Requirement text MUST NOT exceed 500 characters |
| Scenario coverage | Each Requirement MUST have at least 2 Scenarios (happy path + edge case) |

### Referential Integrity

| Check | Rule |
|-------|------|
| Capability → spec mapping | Every capability in proposal.md `## Capabilities` MUST have a corresponding `specs/<capability-name>/spec.md` |
| Spec → capability mapping | Every `specs/<name>/` directory MUST correspond to a capability in proposal.md |
| Spec → task coverage | Every spec Requirement MUST be traceable to at least one task in tasks.md (by keyword or description overlap) |

---

## Output Format

```
## Validation Report: <change-name>

### Results

[For each file/check, show result with icon:]
✓ proposal.md — all checks passed
✗ design.md — 2 errors
  ✗ Missing `## Risks / Trade-offs` section
  ✗ Decision "API Design" has no alternatives mentioned
✓ specs/user-search-api/spec.md — all checks passed
✗ specs/user-search-ui/spec.md — 1 error
  ✗ Requirement "Search input field" has only 1 scenario (minimum 2)
✓ tasks.md — all checks passed
✓ Referential integrity — all checks passed

### Summary

Errors: N | Warnings: N
Total tasks: N (N complete, N pending)

### Verdict

✗ FAIL — N errors. Fix all errors before implementation.

OR

✓ PASS — 0 errors (N warnings — advisory, review but not blocking)
  Ready for implementation. Run `/apply <name>` to start.
```

---

## Guardrails

- Read ALL artifact files before generating the report (don't fail fast on first error)
- Report ALL issues found, not just the first one per file
- Group issues by file for readability
- Always show the summary and verdict
- On PASS, suggest running `/apply <name>`
- On FAIL, list specific fixes needed
- Never modify artifact files — this is read-only validation
- If `feature-spec/changes/<name>/` doesn't exist, show helpful error with available changes
