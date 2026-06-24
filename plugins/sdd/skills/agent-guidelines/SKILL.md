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
- Do NOT add a new dependency for what a few lines or an already-installed package can do.

Before writing custom code, stop at the first rung that holds:

1. **Does this need to exist?** Speculative need → skip it, say so in one line (YAGNI).
2. **Standard library does it?** Use it.
3. **Native platform feature covers it?** Use it (a DB constraint over app code, CSS over JS, `<input type="date">` over a picker lib).
4. **Already-installed dependency solves it?** Use it.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

**The ladder runs *inside* the project's conventions, never above them** — it chooses only among options that already match how this codebase does the same thing (see *Match Existing Code Before Writing* below). When the local precedent is more verbose than a stdlib/native shortcut, the precedent wins: flag the divergence in your report if you think it matters, but do NOT silently introduce a leaner-but-foreign pattern. Correctness, trust-boundary validation, security, and accessibility are never traded for brevity.

Self-check: *"Would a senior engineer call this overcomplicated?"*

## Match Existing Code Before Writing (MANDATORY)

The spec tells you **WHAT** to build; the existing codebase tells you **HOW this project builds it**. Functionally-correct code that ignores local convention is a defect here — it makes the codebase feel inconsistent. The anchor is **how the project performs each technical operation**, NOT "the nearest feature that looks like mine". Before writing any new code:

1. **Decompose the task into its technical operations.** List the concrete operations the code will perform — e.g. *hits the database*, *registers/injects a dependency*, *defines a domain class/aggregate*, *exposes an endpoint*, *splits a layer/module*, *places a new file*, *handles an error*, *logs*, *validates input*. This per-operation list — not a single feature-sibling — is your conformance checklist.
2. **For EACH operation, find how this project already does THAT operation, and mirror the mechanism.** Search by the *operation*, not by feature name: to add DB access, grep how other code reaches the DB (stored procedure? repository? query helper?) and copy that mechanism; to inject a service, copy how DI is wired elsewhere; to write a class, mirror how sibling classes of that kind are structured; to place a file, follow where the same *kind* of file already lives. A `Reference:` line named in the task (it may map a precedent **per operation** — `DB access → …`, `DI → …`) is a useful starting point, but treat each pointer as one anchor among many — resolve every operation against the closest real precedent for *that operation*, even if it lives in an unrelated feature. Mirror the **approach**, not just formatting:
   - **Data access** — same mechanism as existing data access (stored procedures / repository / query helper, never inline SQL or direct `DbContext` if the project avoids them); same read-query conventions (locking hints like `NOLOCK`/`unlock`, pagination shape).
   - **Dependency injection / wiring** — registered and injected the same way the project wires its services (constructor injection via interface, the same DI registration site and style).
   - **Class / type shape** — same structure, base types, immutability, and member organization as sibling classes of that kind.
   - **Structure, layering & file placement** — same separation, and put a new file in the directory where the same *kind* of file already lives.
   - **Naming, error handling, validation, logging** — same patterns the existing code uses for the same operation.
3. **When 3+ places already do an operation one way, do it the same way** — do not introduce a "better" alternative in isolation. If you genuinely believe the established pattern is wrong, flag it (`CONFLICT:`); do not silently diverge.
4. **Changing the architecture does NOT license a new coding style.** When the task restructures existing code there may be no feature-sibling doing the same job — that is expected and is NOT permission to fall back to generic style. The repo still performs every underlying operation (DB access, DI, class definition, file placement, error handling) *somewhere*; anchor each operation to those existing instances. **Fall back to general best practice per-operation, and only when THAT specific operation has no precedent anywhere in the repo** — never because "no sibling feature exists". Local convention always wins over generic advice and over your own preferences.

Self-check before reporting done: *"For every technical operation my code performs — DB access, DI, class shape, file placement, error handling — does it match how this project already does that operation?"*

## Exhaustive Scanning (Zero Misses)

**ZERO MISSES (highest priority):** Before acting on any task, exhaustively scan all files in scope. No scope specified → scan entire project. Scope specified → every file within it. Open and read files to confirm — never rely on filename guessing alone.

## Language

- **Output**: Traditional Chinese
- **Code, comments, and documentation**: English

## Signaling Unknowns — do NOT guess (universal)

When you cannot complete something correctly, emit the matching signal and stop that item instead of inventing an answer. The orchestrator that dispatched you handles each signal; you do not need to know how. These apply in every mode (`/apply`, `/quick`, `/propose`, `/review`).

- **`NEEDS: <precise question + why it blocks you + the options you can see>`** — a fact you need is genuinely *not obtainable from this repo or the context you were given*: a runtime/production value (e.g. the current value of a config flag / feature toggle in an environment), a contract owned by another repo or service, or live infrastructure state. Finish and commit whatever you safely can, then emit NEEDS for the blocked part and stop it. The orchestrator resolves it and resumes you **with your context intact** — continue from there; do not start over.
  **Boundary (strict):** NEEDS is ONLY for facts unobtainable from the repo + provided context. Anything discoverable by reading code, grepping the repo, or following the design/specs you were given is NOT a NEEDS — find it yourself. NEEDS is not an escape hatch for investigation you should do.
- **`CONFLICT: <what the spec/design says> vs <what you'd do> because <reason>`** — the spec or design directs you to do something you believe is wrong or self-contradictory. Do NOT silently override it; emit CONFLICT so the orchestrator can resolve it with the user.
- **`BLOCKED: <reason>`** — you cannot proceed and it is NOT an external fact: the context you were given is wrong/insufficient, the task is too large to do as one unit, or the plan itself is unsound. The orchestrator will re-scope, re-dispatch with corrected context, or escalate. (Difference from NEEDS: BLOCKED gets a fresh re-dispatch; NEEDS gets resolved-and-resumed with your work preserved.)

Anything merely *ambiguous* (more than one reasonable reading, none blocking) is none of these — make the reasonable choice and note it in your report. Reserve the signals for genuine stops.

## Spec-Driven Input

When receiving spec artifacts from `/apply`:

1. Read assigned `specs/<capability>/spec.md` files — WHEN/THEN scenarios are your acceptance criteria
2. Follow `design.md` decisions exactly — do NOT deviate from chosen approaches
3. Implement tasks from `tasks.md` in order, each scoped to one commit
4. Do NOT ask questions — specs are complete. If something is merely ambiguous, make a reasonable decision and flag it; if you hit a genuine stop, use the matching signal from **Signaling Unknowns** above (`NEEDS` / `CONFLICT` / `BLOCKED`)
