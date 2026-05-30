---
name: agent-guidelines
description: >
  Universal behavioral guidelines for ALL agents. Covers coding discipline (think before coding,
  simplicity first), exhaustive scanning (zero misses), language conventions, and spec-driven input rules.
  MUST be loaded when: dispatching any agent for implementation, review, or analysis tasks.
user-invocable: false
---

# Agent Guidelines

**Universal rules for every agent in the team. Internalize these before starting any task.**

## Coding Discipline

### 1. Think Before Coding

Surface assumptions and uncertainties — do NOT proceed silently with interpretations.

- **State your assumptions explicitly** before implementing. If uncertain, ask or flag it.
- **Present multiple interpretations** when a requirement is ambiguous — do NOT silently pick one.
- **Suggest simpler approaches** when the proposed approach seems over-engineered.
- **Stop and name the confusion** when something is unclear, rather than guessing.

### 2. Simplicity First

Minimum code that solves the stated problem. Nothing speculative.

- Do NOT add features beyond what was requested.
- Do NOT create abstractions for single-use code.
- Do NOT add unrequested flexibility or configurability.
- Do NOT add error handling for scenarios that cannot happen.

Self-check: *"Would a senior engineer call this overcomplicated?"*

## Match Existing Code Before Writing (MANDATORY)

The spec tells you **WHAT** to build; the existing codebase tells you **HOW this project builds it**. Functionally-correct code that ignores local convention is a defect here — it makes the codebase feel inconsistent. Before writing any new code:

1. **Find the nearest precedent.** If the task names a `Reference: <path>`, open it first to align on the project's overall approach. Treat it as a **starting anchor, not a cage** — it is picked at design altitude and may not be the closest match for every construct you write. For each specific construct (a query of this kind, a guard of this kind, a sibling class), still locate 1–3 existing implementations of the *same kind of thing* and mirror the closest one; if you find a clearly better-fitting analog than the named Reference, follow that instead. If no Reference is named, do this lookup from scratch.
2. **Mirror their approach**, not just their formatting:
   - **Data access** — if siblings go through stored procedures / a repository layer / a query helper (and never inline SQL or direct `DbContext`), do the same. If reads use a specific hint or pattern (e.g. a `WITH (NOLOCK)` / `unlock`-style convention), follow it.
   - **Structure & layering** — same file layout, same separation (controller → service → repo, composable → store, etc.).
   - **Naming** — class/method/file naming follows the sibling's scheme exactly.
   - **Error handling, validation, logging, DI registration** — same mechanisms the neighbors use.
3. **When 3+ siblings already implement a feature one way, implement the new one the same way** — do not introduce a "better" alternative pattern in isolation. If you genuinely believe the established pattern is wrong, flag it; do not silently diverge.
4. **Only fall back to general best practice when no local precedent exists.** Local convention always wins over generic advice and over your own preferences.

Self-check before reporting done: *"If a reviewer put my file next to the nearest existing analog, would they look like the same author wrote them?"*

## Exhaustive Scanning (Zero Misses)

**ZERO MISSES (highest priority):** Before acting on any task, exhaustively scan all files in scope. No scope specified → scan entire project. Scope specified → every file within it. Open and read files to confirm — never rely on filename guessing alone.

## Language

- **Output**: Traditional Chinese
- **Code, comments, and documentation**: English

## Spec-Driven Input

When receiving spec artifacts from `/apply`:

1. Read assigned `specs/<capability>/spec.md` files — WHEN/THEN scenarios are your acceptance criteria
2. Follow `design.md` decisions exactly — do NOT deviate from chosen approaches
3. Implement tasks from `tasks.md` in order, each scoped to one commit
4. Do NOT ask questions — specs are complete. If genuinely ambiguous, skip and flag it
