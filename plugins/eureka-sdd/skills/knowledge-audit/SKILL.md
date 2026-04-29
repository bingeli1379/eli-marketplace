---
name: knowledge-audit
description: >
  Audit knowledge.md entries against current codebase.
  Verifies domain rules, dev tips, and gotchas are still accurate.
  Use periodically or when major refactoring is done.
user-invocable: true
---

Full audit of `feature-spec/knowledge.md` — verify every entry against the current codebase and clean up stale information.

---

**Input**: None required. Optionally specify a section to audit (e.g., `/knowledge-audit "Dev Environment"`). If omitted, audit all sections.

**Steps**

1. **Locate and read `feature-spec/knowledge.md`**

   Look for `feature-spec/knowledge.md` first.

   **Legacy fallback (silent migration)**: if `feature-spec/knowledge.md` is not found but `./knowledge.md` exists, run `git mv ./knowledge.md feature-spec/knowledge.md` (fall back to `mv` if untracked), announce `Moved knowledge.md → feature-spec/knowledge.md (legacy location migration)`, then proceed using the moved file.

   **If neither exists:** Report "No knowledge.md found in `feature-spec/` or project root. Nothing to audit." and stop.

   **If found:** Read the entire file. Parse entries by section (Domain, Dev Environment, Gotchas, External Dependencies, or any custom sections).

2. **Verify each entry against the codebase**

   For each entry, determine its verification strategy:

   **a. File/path references** (e.g., "edit `mocks/api/user.json`")
   - Check if the referenced file exists
   - If the file exists, check if the described content/behavior is still accurate

   **b. Env var references** (e.g., "set `MOCK_STYLE=true` in `.env.local`")
   - Search for the env var in the codebase (grep for the variable name)
   - Verify it's still used and the described behavior is accurate

   **c. Domain rules** (e.g., "VIP users get 3-day grace period")
   - Search for related code (keywords, function names, constants)
   - Verify the rule is still reflected in the implementation

   **d. External dependencies** (e.g., "calls PaymentGateway API at `/api/v2/charge`")
   - Search for the referenced endpoint/service in the codebase
   - Verify it's still referenced and the description is accurate

   **e. Process/workflow knowledge** (e.g., "must run migration before seeding")
   - Verify the described steps are still relevant by checking related files

   Rate each entry:
   - **✓ Verified** — still accurate, evidence found in codebase
   - **⚠ Possibly outdated** — related code changed or evidence is ambiguous
   - **✗ Stale** — referenced entity no longer exists or behavior clearly changed

3. **Present audit report**

   ```
   ## Knowledge Audit Report

   ### ✓ Verified (N entries)
   - [entry summary] — verified via [evidence]

   ### ⚠ Possibly Outdated (N entries)
   - [entry summary] — reason: [what changed]

   ### ✗ Stale (N entries)
   - [entry summary] — reason: [referenced file/var/endpoint no longer exists]

   **Score: X/Y entries verified (Z%)**
   ```

4. **Resolve outdated and stale entries**

   For each ⚠ and ✗ entry, use **AskUserQuestion**:

   Present all flagged entries at once:
   ```
   The following entries need attention:

   1. ⚠ "Mock style X: change ENV_Y" — ENV_Y no longer referenced in code
   2. ✗ "Edit mocks/api/user.json for test data" — file deleted
   3. ⚠ "VIP grace period is 3 days" — constant changed to 5 days

   For each, choose: Update / Remove / Keep
   (e.g., "1: update, 2: remove, 3: update")
   ```

   **For "Update":**
   - Propose the corrected entry based on current codebase state
   - Apply the update to knowledge.md

   **For "Remove":**
   - Delete the entry from knowledge.md

   **For "Keep":**
   - Leave unchanged (user knows better — maybe the code is wrong, not the knowledge)

5. **Commit if changes were made**

   If any entries were updated or removed:
   - Stage `feature-spec/knowledge.md`
   - Commit: `docs: audit knowledge.md, update N entries, remove M stale`
   - Do NOT push to remote

   If no changes: Report "All entries verified. No changes needed." and stop.

---

## Guardrails

- Read the FULL codebase context for each entry — don't just grep for one keyword
- When rating as ⚠, explain what changed so the user can make an informed decision
- Never auto-remove entries — always confirm with user
- "Keep" is a valid choice — the user may have context you don't
- For large knowledge.md files, process section by section to manage token usage
- If a section is specified in input, only audit that section
- Commit message should reflect the actual changes made
