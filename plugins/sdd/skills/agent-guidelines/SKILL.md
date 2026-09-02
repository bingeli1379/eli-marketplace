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

### 3. Comments: default to none

Write a comment only for business logic that the code cannot carry on its own. If naming makes the intent clear, there is no comment to write. Never restate what the line does.

**The failure mode to avoid is over-commenting, not under-commenting.** When you are working from a design document, its rationale is the strongest pull toward writing too much: the decisions feel important, so they get copied into the code as defensive paragraphs. Resist it — **the design document is where rationale lives, and it is already written down.** In code, state the constraint in one line and point at the document (`(see design.md D4)`) instead of reproducing the argument for it.

Concretely, do NOT write:
- the *reasoning* behind a decision — why an alternative was rejected, what the numbers were, what would break otherwise;
- history — what the code used to do, what a review round changed, why a limit was chosen;
- a summary of the block that follows it.

DO write, in one or two lines:
- a constraint that is invisible in the code and would be undone by an innocent-looking edit (e.g. a parameter deliberately absent, a property deliberately nullable);
- a domain rule the reader cannot infer (e.g. why a status is excluded);
- a deliberate deviation from the obvious approach, when the reader would otherwise "fix" it.

Self-check: *"If I deleted every comment I just wrote, what would a reader actually get wrong?"* Keep only those.

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

### Decision order when modifying existing code

Local precedent (above) is step one, but it does not settle a framework API you are unsure of. Before committing to an approach:

1. **Read** the surrounding code — same file plus sibling files in the same directory — for naming, patterns, and error-handling style.
2. **Look up** when the change involves framework API usage or a pattern choice: consult an available up-to-date documentation tool (e.g. a `context7`-style docs MCP — `resolve-library-id` → `query-docs`) for the current recommended approach. If no such tool is wired in this environment, skip this step and rely on the repo's own precedent; do NOT treat a missing docs tool as a blocker.
3. **Decide** by priority: **project convention > official recommendation > your own judgment.** Check convention first, *then* take the simplest option that matches it (the Simplicity First ladder above).
4. **Implement.**
5. **Verify** — does the new code match surrounding style? Did you introduce a pattern the file did not already use?

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

**A missing backing service is a `NEEDS`, and provisioning one is not your job.** When a command needs infrastructure that is not up — a database, a broker, a container stack — make **one** attempt with whatever the project documents, and if it does not come up, emit `NEEDS` naming the service and the actual error. Do not retry the bring-up, and do not go debugging image tags, credentials, or ports: a stale image reference or an unreachable registry is environment state you cannot fix from inside the repo, so each retry spends minutes and changes nothing. Then **do not run the command that needs it anyway** — a suite whose dependency is down retries the connection instead of failing, so it hangs with no output and looks merely slow. Verify what you can without the dependency (a filtered run that needs none of it, a build), report those results plainly as partial, and say which check is still owed. **Never report a suite as passing when you did not see it pass.**

**An unreachable external system is not automatically a stop — when you hold its contract, stub it and finish the path.** Implementation dispatches only, since it is about code you were sent to write; a reviewer has nothing to stub. Distinct from the paragraph above: that one is infrastructure your *tests* need brought up, this one is a third-party the *code* calls (a translation service, a payment gateway, a mail provider, any API whose request/response shape is in the design, the specs, or an existing client in the repo). There the missing piece is a credential or an endpoint, not knowledge — so implement the real call site against a stub at the project's own seam (the interface, client or factory the repo already injects), test it, commit it, and report `MOCKED: <what is stubbed> · <the single swap the user performs> · <how they check it worked>`. The orchestrator carries that line into its handoff block. Emitting `NEEDS` instead leaves the whole path unwritten to save one value, and a task deferred whole is a task nobody finishes.

**The stub is never passed off as the real thing.** It is visible in the code as a stub, the report says the path is unverified against the live system, and no test asserting the real integration is marked passing. Where the contract itself is what you lack — you would be inventing the response shape rather than filling in an address — that is a `NEEDS` and the rule above does not apply.

## Completion Contract — do NOT end your turn early

Applies whenever you were dispatched with a **list of tasks to implement** (`/apply` and `/quick` worker dispatches). Reviewers, whose deliverable is a verdict rather than commits, are bound instead by the verdict rules in their own dispatch.

You are NOT finished until **every** assigned task is committed and you have printed a `DONE: <task-number> <task-description>` line for each. Do NOT stop to "report progress" and wait for further instructions — complete all your tasks within this turn.

The ONLY valid early stops are the three signals above: `NEEDS:` / `CONFLICT:` / `BLOCKED:`. Going idle or yielding without one of {all tasks DONE, NEEDS, CONFLICT, BLOCKED} is a protocol violation, not a pause — the orchestrator treats it as a failed dispatch and re-dispatches, discarding the turn.

**"Waiting to be notified" is not a fourth signal.** Yielding on the belief that something will wake you — a backgrounded command, a monitor, a watcher — ends your turn with the work uncommitted, and the orchestrator has no way to tell that from a crash. If you genuinely cannot proceed, one of the three signals says so; nothing else does.

**Never hold a commit hostage to a verification.** Commit the work first, then verify, and report what the verification said — in that order. Gating the commit on a check that turns out not to finish is how completed, correct work is lost: the run ends with a passing edit sitting uncommitted in the tree, and only luck recovers it. A verification that cannot complete is a `NEEDS` **with the work already committed**, never a reason to sit on it. And do not poll a hung command hoping it resolves — a run producing no output for many times its known duration has lost a dependency, which no amount of waiting restores.

(In **no-git** mode there is nothing to commit to: implement directly, skip the per-task commits, and still print a `DONE:` line per task.)

## Spec-Driven Input

When receiving spec artifacts from `/apply`:

1. Read assigned `specs/<capability>/spec.md` files — WHEN/THEN scenarios are your acceptance criteria
2. Follow `design.md` decisions exactly — do NOT deviate from chosen approaches
3. Implement tasks from `tasks.md` in order, each scoped to one commit
4. Do NOT ask questions — specs are complete. If something is merely ambiguous, make a reasonable decision and flag it; if you hit a genuine stop, use the matching signal from **Signaling Unknowns** above (`NEEDS` / `CONFLICT` / `BLOCKED`)
