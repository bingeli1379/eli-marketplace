---
name: engineering-checklist
description: >
  Mandatory principles and checklist for ALL engineers (frontend & backend) when writing or modifying code.
  MUST be loaded when: implementing tasks, fixing bugs, refactoring code, or reviewing code.
  Covers rename completeness, import integrity, dead code cleanup, test hygiene, and where a
  validation check belongs.
user-invocable: false
---

# Engineering Checklist

**Derived from real-world production bugs. Applies to ALL engineers — frontend, backend, Electron, and reviewers.**

## Principles — follow these while writing code

1. **Match existing patterns over "best practice"** — before writing any new file/query/function, open at least one sibling of the same kind and mirror its style (locking hints, `SELECT` shape, file structure, naming). Consistency outweighs theoretical improvements. Deviations must be stated up front, not silently introduced.
2. **Run the linter** — if the project has a linter configured, run it after every change and fix errors before committing; no lint rules disabled without justification
3. **Every rename must be total** — grep the entire codebase for the old name; string literals, dynamic refs, and config keys are easy to miss
4. **Delete, don't comment out** — removed features = delete ALL related code (components, routes, tests, styles, configs)
5. **Imports are a contract** — after deleting/moving an export, update all importers yourself
6. **Tests must stay clean** — delete old test files when replacements exist; fix the type instead of `as any`
7. **One bug means many bugs** — grep the full codebase for the same pattern; fix all occurrences, not just the one you found
8. **Bulk changes require bulk verification** — glob/grep for remaining instances; "it compiled" is not proof of correctness
9. **Guard at the trust boundary, nowhere else** — a check belongs where the value *enters*, and only when its source can actually send something wrong. Three sources, three answers:
   - **Written into the code** (a const, a timeout on a model, a factory default) → **no check at all.** The only "input" is the next engineer editing that line, and the type plus the diff already cover it; a branch that can never be true just makes the next reader ask whether it can. Observed: a hardcoded timeout gained a negative-value check on the consuming side, three lines below the literal it guards, where the framework would have thrown anyway.
   - **Config / env** → validate **once at startup and fail fast**, never on each use, and validate what actually breaks: a unit mismatch (`30` read as ms when seconds were meant) passes every sign and range check ever written.
   - **A request from outside the trust boundary** → validate, using the project's existing contract mechanism.

   **A developer-facing API is not a trust boundary because it has a form in front of it.** A Swagger-driven internal/admin endpoint does not need field-shape validation on its inputs — a max length, a format regex, a numeric range — beyond what the type already enforces; authn/authz is what keeps the wrong caller out, and whoever can reach that form can read the code. Full field validation is for an actual end-user-facing form (marketing, customer input). **A library's or plugin's public API is the opposite case, developer-facing though it is** — a JS caller or an `as`-casted TS one sends whatever it likes and the type never runs, so that entry point IS a boundary and keeps its runtime guards; `frontend-checklist` principle 11 owns the shape they take. **This governs the check you are about to write, never one already in the code** — an existing guard stays, since it may be load-bearing for a reason no longer visible (`agents/review-engineer.md` treats removing one as a finding in its own right), and where the surrounding code guards these values by convention, **principle 1 outranks this one**: match the convention and note the divergence in your report instead of breaking the pattern. **This binds reviewing as much as writing, wherever this file is loaded: a missing guard on a non-boundary value is not a finding** — raising it spends a fix round adding dead code. Two things it does not touch: a genuine boundary, injection, or resource-exhaustion finding, and a bound that exists because the **sink** is bounded — an open-ended field (a remark, a note, a description) written to a fixed-width column is a correctness concern at any exposure, with no attacker required (`agents/security-engineer.md` routes exactly that case to review-engineer).

---

## Post-Implementation Checklist — verify after writing code

### Existing Conventions Respected

- [ ] Opened a sibling file and confirmed the new code looks like it belongs next to it
- [ ] If a better pattern was introduced, ALL affected code updated — no mixed state left behind
- [ ] Every check added was traced to where its value enters — none guards a value that cannot vary at runtime (principle 9, *Guard at the trust boundary*)

### Rename / Move Completeness

- [ ] **Grep the ENTIRE codebase** for the old name — every occurrence updated or confirmed irrelevant
- [ ] Import paths updated in ALL files that reference the renamed/moved file
- [ ] Type references updated after interface/type/class renames
- [ ] String literals containing the old name (route paths, API URLs, event names, config keys) updated
- [ ] Test files and documentation updated to use the new name

### Import & Reference Integrity

- [ ] All functions/variables used in code have corresponding imports or are in scope
- [ ] After deleting or moving an export, all importers grepped and updated
- [ ] No circular import chains introduced

### Dead Code Cleanup

- [ ] Old files deleted when replacements exist (e.g., `.js` deleted when `.ts` equivalent exists)
- [ ] Removed features have ALL related code deleted (components, routes, tests, styles, configs)
- [ ] Commented-out code, unused imports, unused variables/functions removed

### Test Hygiene

- [ ] Old test files deleted when new equivalents exist (no double test runs)
- [ ] Unnecessary `@ts-expect-error` / `@ts-ignore` removed after underlying issue is fixed
- [ ] No type-casting band-aids (`as any`) — actual type issue fixed

### Bug Pattern Sweep

- [ ] When a bug is found/fixed, grepped the ENTIRE project for the same pattern
- [ ] All occurrences of the same bug type fixed — not just the one originally discovered
- [ ] If the bug was in generated/migrated code, checked ALL generated/migrated files

### Bulk Change Verification

- [ ] EVERY file in scope was processed — glob/grep confirms no remaining instances
- [ ] Spot-checked at least 3 files from different directories
- [ ] Full test suite passes
- [ ] **Stop when tests pass** — do not refactor, optimize, or "improve" passing code unless explicitly tasked
