---
name: systematic-debugging
description: >
  Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes.
  Enforces root cause investigation through 4 phases: reproduce, gather evidence, analyze, verify.
  MUST be loaded when: debugging issues, fixing test failures, investigating unexpected behavior.
user-invocable: false
---

# Systematic Debugging

Find the root cause before changing code. A fix that lands before the cause is known is a guess with a commit message; when it happens to work, nobody can say why, and the next symptom starts from zero.

Applies to any technical issue — test failures, production bugs, performance problems, build and integration failures — and most to the cases where skipping it is tempting: under time pressure, when the fix looks obvious, and after a previous fix did not hold.

## Phase 1: Root cause investigation

1. **Read the error in full** — the whole stack trace, line numbers, file paths, error codes. Warnings included.
2. **Reproduce it in a tight, red-capable loop.** Before theorising, build one command that goes red on *this* bug and green once fixed — a failing test, a curl, a CLI snapshot, a replay. Bisection, hypothesis testing and instrumentation all consume that loop; without it there is nothing to test against. Construction taxonomy, how to tighten it, the perf-regression variant and the completion gate: `${CLAUDE_SKILL_DIR}/feedback-loop.md`. Not reproducible → gather more data; do not guess.
3. **Check what changed** — recent commits, new dependencies, config, environment differences.
4. **In a multi-component system, locate the failing layer before touching any of them.** Log what enters and leaves each component boundary (data, env, config propagation), run once, and read where the chain breaks; investigate that component only.
5. **Trace a bad value to its origin** when the error is deep in the call stack — fix where it is produced, not where it is caught. Full technique: `${CLAUDE_SKILL_DIR}/root-cause-tracing.md`.

## Phase 2: Pattern analysis

Find working code in the same codebase that does what the broken code should, read the reference implementation completely, and list every difference — however small. The difference you dismissed as irrelevant is the usual culprit.

## Phase 3: Hypotheses

1. **Generate 3–5 ranked hypotheses, not one.** A single hypothesis anchors on the first plausible idea. Each must be **falsifiable** — state the prediction it makes ("if X is the cause, changing Y makes the bug disappear"); one that predicts nothing is discarded or sharpened.
2. **Show the ranked list to the user before testing.** They re-rank instantly with domain knowledge ("we just deployed a change to #3") or rule one out. Do not block on it — proceed with your ranking if the user is not there.
3. **Test the top hypothesis with the smallest change that can refute it**, one variable at a time. Refuted → next hypothesis; never stack a second change on top of an unconfirmed first.
4. When you do not understand something, say which thing — "I don't understand X" — instead of proceeding as though you did.

## Phase 4: Fix

1. **Write the failing test first** (per `test-driven-development`): the simplest reproduction, automated where a framework exists, a one-off script otherwise.
2. **One fix, addressing the identified cause.** No bundled refactoring, no "while I'm here".
3. **Verify** — the new test passes, the existing suite still passes, the original symptom is gone.
4. **A fix that does not work sends you back to Phase 1 with the new information.** After **three** failed fixes, stop fixing: each fix revealing new coupling elsewhere, or needing a large refactor to land, is a wrong architecture rather than a wrong hypothesis. Name the pattern and discuss it with the user before a fourth attempt.

## When the process finds no root cause

An issue that is genuinely environmental, timing-dependent, or external gets appropriate handling (retry, timeout, error message) plus the monitoring or logging that would catch it next time — and a record of what was investigated. Reach that conclusion only after the phases above; most "no root cause" verdicts are an investigation that stopped early.

## Supporting techniques

Each at `${CLAUDE_SKILL_DIR}/<file>`:

- **`feedback-loop.md`** — construct, tighten, and gate the red-capable reproduction loop (Phase 1's core move)
- **`root-cause-tracing.md`** — trace bugs backward through the call stack to the original trigger
- **`defense-in-depth.md`** — add validation at multiple layers after the root cause is found
- **`condition-based-waiting.md`** — replace arbitrary timeouts with condition polling

Related skills: `sdd:test-driven-development` (the failing test in Phase 4), `sdd:verification-before-completion` (evidence before claiming the fix worked).
