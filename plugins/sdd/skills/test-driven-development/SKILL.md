---
name: test-driven-development
description: >
  Use when implementing any feature or bugfix, before writing implementation code.
  Enforces RED-GREEN-REFACTOR cycle: write failing test first, minimal code to pass, then refactor.
  MUST be loaded when: implementing new features, fixing bugs, writing any production code.
user-invocable: false
---

# Test-Driven Development (TDD)

Write the test first, watch it fail, write the minimal code that passes, then refactor.

**Core principle:** a test you never saw fail has not proved it can catch the bug. Production code counts as covered only once a test for it has been seen **red** and then **green** — this is the invariant, and it is what everything below protects. Code written before its test is not covered yet: write the test, make it fail against the code (revert or disable the behaviour it checks), then restore and watch it pass. Keeping the code is fine; skipping the red is not.

## When to use

Every feature, bug fix, refactor, and behaviour change.

**Exceptions** — ask the user, or, when dispatched under `/apply` / `/quick` where questions are forbidden, decide per `agent-guidelines` → *Spec-Driven Input* and flag the choice in your report: throwaway prototypes, generated code, configuration files.

**One exception already decided upstream:** a **walking-skeleton group** — a task group whose stated job is to prove a cross-layer integration path with placeholder data, explicitly marked `SKELETON:` and scheduled to be replaced by later harden groups. It is a disposable integration probe, not production code. The decision is recorded in `design.md` and visible to the user before implementation starts, so as the implementer you neither choose it nor re-confirm it. See *Walking Skeleton* below; everything outside such a group follows the core principle in full.

## Red → Green → Refactor

### RED — write one failing test

One behaviour, a name that states it, against real code (mocks only when unavoidable — a test that asserts on a mock's call count tests the mock).

### Verify RED — watch it fail

Run the project's own test command (the `verification_commands` entry when one is configured). Confirm it **fails** rather than errors, and fails because the behaviour is missing, not from a typo. A test that passes here is testing existing behaviour — fix the test. A test that errors is fixed and re-run until it fails correctly.

### GREEN — the simplest code that passes

Just enough to pass this test: no extra parameters, options, or generality the test did not ask for, no refactoring of other code.

### Verify GREEN — watch it pass

Same command. The new test passes, the other tests still pass, the output is clean of errors and warnings. The test fails → fix the code, not the test. Another test fails → fix it now, before the next cycle.

### REFACTOR — after green only

- Remove duplication, improve names; keep the tests green and add no behaviour.
- Extract a helper only where this change gives it a second caller — a one-caller helper reads worse than the lines it hides, and a design that described the behaviour did not ask for the function.
- Delete every comment written in RED/GREEN that fails the `agent-guidelines` self-check (*what would a reader get wrong without it?*) — the pull to explain a design decision in code is strongest right after implementing it, so this pass is where those paragraphs go.

Then the next failing test.

## Anti-pattern: horizontal slicing

**Do not write all the tests first, then all the implementation.** Tests written in bulk verify *imagined* behaviour: they test the shape of things (signatures, data structures) rather than what the code does, pass when behaviour breaks and fail when it is fine, and commit you to a test structure before the implementation has taught you anything.

```
WRONG (horizontal):           RIGHT (vertical, tracer bullets):
  RED:   test1..test5           RED→GREEN: test1→impl1
  GREEN: impl1..impl5           RED→GREEN: test2→impl2
                                RED→GREEN: test3→impl3
```

One test → one implementation → repeat; each test responds to what the previous cycle showed. The first cycle is the **tracer bullet** that proves the path end-to-end before coverage widens. This bites hardest in `/apply`, where an agent holding a whole task group is tempted to batch its tests up front.

## Walking Skeleton (integration probe — a different axis, not an exception to vertical slicing)

**Do not confuse this with the anti-pattern above.** They are orthogonal:

| | axis | what it says |
|---|---|---|
| Horizontal slicing (anti-pattern) | tests vs implementation | never batch all tests, then all impl — go one behaviour at a time |
| Walking skeleton (this section) | across architectural layers | when integration risk is unproven, first prove the whole path end-to-end with placeholder data, then fill each layer in |

A walking skeleton is the *tracer bullet* above widened to the whole system: instead of proving one behaviour end-to-end inside one layer, it proves the **wiring across every layer** before any layer is real. It is chosen at design time (the architect's *Implementation Strategy Selection*, recorded in `design.md` `## Decisions`), not improvised mid-task.

### When it applies

**You do not decide this — `design.md` already did.** The strategy is picked at design time against the criteria in the architect's *Implementation Strategy Selection* (the single authority for that test; Contract-First is the default). If `design.md` does not name Walking Skeleton, this whole section does not apply and the core principle governs every line you write. If it does, the rules below are binding for the skeleton group only.

### Rules inside a skeleton group

1. **No unit TDD for the placeholder code.** The skeleton is a disposable probe; unit tests written against placeholder returns test nothing and get deleted with them. This is the exception named in *When to use* above.
2. **The integration path itself must be proven**, not assumed — the group is not done until the end-to-end path actually runs (a request reaching the UI, an IPC round-trip completing, a signal arriving). Proving it by hand is acceptable; proving it with one end-to-end test is better.
3. **Every placeholder MUST carry a `SKELETON:` marker comment** (e.g. `// SKELETON: replace in harden phase`) — in the **source file's comment syntax**, never in markdown or docs (the completion gate excludes `*.md` precisely so documenting the convention does not trip it). This is what the harden groups and `/complete`'s completion gate locate.
4. **Every `SKELETON:` site MUST have a harden task** that replaces it with the real implementation — and that harden work is **full TDD, no exception**: RED → GREEN → REFACTOR, vertical slices, per rules above.
5. **Residual `SKELETON:` markers mean the change is unfinished.** `/complete` blocks on them. A skeleton that shipped is a bug, not a shortcut.

## Done when

- Every new behaviour has a test that was seen red, then green, for the expected reason.
- The full suite passes with clean output; tests exercise real code, edge cases and error paths included.
- A walking-skeleton group is checked against rule 2 of *Walking Skeleton* instead — "the end-to-end path actually runs"; every harden group and all other work is checked against this list.

## Bugs

A bug gets a failing test that reproduces it before the fix — the test proves the fix and prevents the regression (`systematic-debugging` Phase 4).

## Testing anti-patterns

When adding mocks or test utilities, read `${CLAUDE_SKILL_DIR}/testing-anti-patterns.md`: testing mock behaviour instead of real behaviour, test-only methods on production classes, mocking without understanding the dependency.
