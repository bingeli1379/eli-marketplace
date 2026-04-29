---
name: engineering-checklist
description: >
  Mandatory principles and checklist for ALL engineers (frontend & backend) when writing or modifying code.
  MUST be loaded when: implementing tasks, fixing bugs, refactoring code, or reviewing code.
  Covers rename completeness, import integrity, dead code cleanup, and test hygiene.
user-invocable: false
---

# Engineering Checklist

**Derived from real-world production bugs. Applies to ALL engineers — frontend, backend, Electron, and reviewers.**

## Principles — follow these while writing code

1. **Respect the existing codebase** — scan existing conventions first; do not leave a mixed state unless it is a planned phased migration
2. **Run the linter** — if the project has a linter configured, run it after every change and fix errors before committing; no lint rules disabled without justification
3. **Every rename must be total** — grep the entire codebase for the old name; string literals, dynamic refs, and config keys are easy to miss
4. **Delete, don't comment out** — removed features = delete ALL related code (components, routes, tests, styles, configs)
5. **Imports are a contract** — after deleting/moving an export, update all importers yourself
6. **Tests must stay clean** — delete old test files when replacements exist; fix the type instead of `as any`
7. **One bug means many bugs** — grep the full codebase for the same pattern; fix all occurrences, not just the one you found
8. **Bulk changes require bulk verification** — glob/grep for remaining instances; "it compiled" is not proof of correctness

---

## Post-Implementation Checklist — verify after writing code

### Existing Conventions Respected

- [ ] Scanned the project's existing patterns before writing code
- [ ] New code follows the same conventions already used in the project (naming, structure, patterns)
- [ ] If a better pattern was introduced, ALL affected code updated — no mixed state left behind

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
