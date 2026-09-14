---
name: verification-before-completion
description: >
  Use when about to claim work is complete, fixed, or passing, before committing or creating PRs.
  Requires running verification commands and confirming output before making any success claims.
  Evidence before assertions, always.
user-invocable: false
---

# Verification Before Completion

A claim of status — tests pass, build succeeds, bug fixed, agent finished — is backed by output produced **in this turn**, or it is not made. Output from an earlier run, a linter's silence, or another agent's "success" is not evidence for it.

| Claim | Evidence it needs |
|-------|-------------------|
| Tests pass | The test command's output from this turn: 0 failures, exit code read |
| Build succeeds | The build command's output: exit 0 (a passing linter says nothing about compilation) |
| Bug fixed | The original symptom re-tested and gone |
| Regression test works | Seen red without the fix, green with it — a test that only ever passed proves nothing |
| Agent completed | The VCS diff shows the change, not the agent's report |
| Requirements met | Each requirement checked off individually, not inferred from a green suite |

When the evidence cannot be produced — the command hangs, a dependency is down, the suite cannot run here — report the actual state and what is still owed, in the words for that (`agent-guidelines` → *Signaling Unknowns*). Partial verification is reported as partial.
