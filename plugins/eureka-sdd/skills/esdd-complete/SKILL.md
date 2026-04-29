---
name: esdd-complete
description: >
  Complete a change: extract knowledge, update docs, then clean up.
  If a name is given, complete that specific change. If omitted, auto-scan
  and batch-complete all fully finished changes.
user-invocable: true
---

Complete a change by extracting valuable knowledge, updating project docs, then deleting the change artifacts.

---

**Input**: Optionally specify a change name (e.g., `/esdd-complete add-user-search`). If omitted, auto-scan for all completed changes.

**Steps**

1. **Select change(s) to complete**

   **If a name is provided:** Use that single change. Go to step 2.

   **If no name is provided (batch mode):**
   - List all directories under `feature-spec/changes/` (excluding `archive/` if it exists)
   - If none exist, report error: "No active changes found."
   - For each change, read its `tasks.md` and count `- [ ]` vs `- [x]`
   - Collect changes where **all tasks are complete** (zero `- [ ]` remaining), or where `tasks.md` does not exist
   - If no changes qualify, report: "No fully completed changes found." and list each change with its completion status (e.g., `add-user-search: 3/5 tasks complete`)
   - If one or more qualify, display them and proceed to complete **all** of them sequentially (steps 2–7 for each)

   **IMPORTANT**: Batch mode does NOT ask for confirmation — it completes all fully finished changes automatically.

2. **Check task completion status**

   Read `feature-spec/changes/<name>/tasks.md`:
   - Count tasks marked `- [ ]` (incomplete) vs `- [x]` (complete)
   - Display: "Tasks: N/M complete"

   **If incomplete tasks found (only possible when name is explicitly provided):**
   - Display warning showing count and list of incomplete tasks
   - Use **AskUserQuestion** to confirm: "Complete with N incomplete tasks?" / "Cancel"
   - Proceed only if user confirms

   **If no tasks.md exists:** Proceed without task-related warning.

3. **Extract knowledge**

   Read all change artifacts:
   - `feature-spec/changes/<name>/proposal.md` — scope and motivation
   - `feature-spec/changes/<name>/design.md` — technical decisions and approach
   - `feature-spec/changes/<name>/tasks.md` — what was implemented
   - `feature-spec/changes/<name>/specs/*/spec.md` — acceptance criteria
   - `git log --oneline` to find this change's commits (match conventional-commit scope to the change name, or take the contiguous range since the last `chore: complete` commit), then `git diff <first-commit>^..HEAD` — actual code changes

   Each knowledge entry is a **pointer, not a paragraph**: one sentence stating a project-specific fact, plus file-path pointers to where the logic lives. Do NOT re-explain the logic — the reader follows the pointer.

   Categories:
   - **Domain**: business rules, conventions
   - **Dev Environment**: mock setup, env flags, test data locations
   - **Gotchas**: non-obvious cross-file coupling, implicit ordering constraints
   - **External Dependencies**: APIs, services, internal packages to prefer

   **Record only if ALL hold**:
   - Fact is **project-specific** — not applicable to any other project
   - A new developer would NOT figure it out by reading the code alone
   - It points to cross-file coupling, a domain rule, or a preferred package

   **Do NOT record**:
   - **Generic knowledge** — anything that applies to any project, language, or framework (e.g., "always verify lockfile after `npm install`", "run tests before merging", "use `command -v` for cross-platform shell")
   - Implementation details derivable from the code itself
   - **Logic walkthroughs** — point to the file, do not repeat the code
   - Fix / verification / debugging recipes — those belong in commits and PRs
   - Information already in CLAUDE.md
   - Temporary or one-off decisions
   - **Speculative / hypothetical entries** — knowledge.md captures past pain only. Drop "if future code does X, do Y" guesses, "for safety we should also Z" hedges, and any sentence you cannot tie to an existing line of code. Keep only the verified fact, or drop the entry entirely.

   **Entry format**:
   - **Write in English** regardless of the user's conversation language
   - **One line per entry**, hard rule. Two lines only when a single fact genuinely needs both (e.g., a coupled pair where each half is meaningless alone). Length smell test: if your entry uses "and", "because", or "when X then Y, when Z then W", it is probably explaining logic — collapse to a pointer or split into separate entries.
   - Merge related facts into a single bullet only when they are inseparable.
   - Template: `<project-specific fact>. <pointer — file path(s) + role>.`
   - Good (concise, pointer form):
     `` `SectionTopPayoutSlots` only renders for `country === 'MM'`. Guard spread across `server/proxies/globalSettingClient.ts`, `composables/useTopPayoutSlots.ts`, `components/section/SectionTopPayoutSlots.vue` — change all three together. ``
   - Bad (logic walkthrough):
     `` Section order config only lists MM and JP; composable hideSection is `country !== 'MM' && country !== 'ID'`; data map has only MM/ID; currency hardcode is `country === 'ID' ? 'IDR' : 'MMK'`. Actual runtime: only MM sees content because... ``
   - Bad (generic): ``After `npm install`, verify lockfile versions match manifest — CI `npm ci` may install the wrong version.``
   - Bad (speculative — drop the "if future" half):
     `` Plugin uses `enforce: 'pre'` for advancedFormat. If future code uses `Q/Qo/Do/X/x` tokens, extend the import. ``
     → Fix: keep only `` `advancedFormat` plugin must run with `enforce: 'pre'`. `nuxt.config.ts:14`. ``

   **Self-filter — apply to each candidate, then write directly without asking the user.** The user will correct after the fact. Do NOT present a list and ask for selection; do NOT use AskUserQuestion here.

   For each candidate:
   1. Project-specific or generic? → drop if generic
   2. Walks through logic or points to it? → trim to pointer form
   3. Can it collapse into one line without losing the fact? → collapse
   4. After all three filters, does anything survive? → if yes, write it; if no, skip silently

   If `feature-spec/knowledge.md` does not exist, create it by copying the canonical skeleton from `plugins/eureka-sdd/templates/knowledge.md` (single source of truth, also used by `/esdd-init`). Do not paraphrase or trim — write it verbatim. The file lives next to `context.md` so all spec-related artifacts sit in one place. The HTML comments under each heading orient new contributors on what belongs where; **keep them in place** when appending new entries.

   **Legacy migration (one-time)**: if `./knowledge.md` exists at the project root from a previous plugin version, treat it as the source of truth and `git mv ./knowledge.md feature-spec/knowledge.md` before appending. If `feature-spec/knowledge.md` already exists too, leave both alone and surface in the summary so the user can resolve manually.

   Append each surviving candidate as a single `- ` bullet under its category. **Preserve the HTML comment block under each heading verbatim** — it is documentation for future contributors, not noise.

   Report what was written in the final summary (step 9). If the user disagrees, they will say so and you can trim or remove.

4. **Update project docs**

   Scan the project root for documentation files: `CLAUDE.md`, `README.md`, `README`, `docs/`.

   For each existing doc file, assess whether this change introduced:
   - **CLAUDE.md**: Architectural changes (new layers, new patterns, new conventions, new commands)
   - **README.md**: Setup changes, new prerequisites, changed workflows, new features visible to users

   **If updates needed:**
   - Show the proposed updates to the user
   - Apply after confirmation (or automatically if changes are minor additions)

   **If no updates needed:** Report "No doc updates needed" and move on.

5. **Sync `feature-spec/context.md`** (auto-apply, no confirmation)

   If `feature-spec/context.md` exists, update its structural sections from this change's diff and `design.md`. The goal: keep the AI-readable map of "where things live" current, so future AI knows where to make changes.

   Read the change diff (`git diff <first-commit>^..HEAD`) and `design.md`, then update each section in place:

   | Section | Trigger | Update |
   |---|---|---|
   | **Architecture Layers** | New top-level src folder that represents a layer (e.g., `src/Application/`) | Add the layer + its responsibility |
   | **Domain-to-Code Map** | New domain folder under `src/` (or rename of an existing one) | Add a row using **pointer form**: `Domain \| path/ \| aggregate root + N items under this path`. Remove the old row on rename. NEVER enumerate the file list. |
   | **Entry Points** | New endpoint group, new `pages/*` directory, new server middleware folder, new plugins/modules/, new worker project, new event handler folder | Add the path. Walk the full Entry Points checklist (HTTP, pages, middleware, plugins, modules, jobs, event handlers, CLI) — do not stop at the first match. |
   | **Conditional Subsystems** | New conditional activation pattern (request-header branching, feature flag gate, route-prefix routing, env-driven subsystem) | Add an entry that states the **trigger condition** (header / flag / path / env), not just the behavior. If the section does not exist yet and a subsystem is detected, create the section. |
   | **Cross-cutting Concerns** | New middleware, new shared composable used in 2+ places, new policy folder | Add the file path + one-line usage rule. If the section grows beyond ~5 items, hoist the heaviest concern (caching, i18n, datetime) into its own H2 section. |
   | **Hard Rules** | `design.md` records a new architectural invariant | **Classify before writing**: structural (true a year from now) → add to Hard Rules; historical (version-pinned, migration leftover, "do not use old X") → append to `knowledge.md/Gotchas` instead and skip Hard Rules. |
   | **Common Commands** | New `package.json` script that developers will run regularly (`dev`, `test`, `lint`, `build`, etc.) | Add the command |
   | **Tech Stack & Versions** | Major dependency upgrade or new framework adopted | Update the line. **Single source of truth**: do not propagate the new version into Mission, Hard Rules, or any other section. |
   | **Glossary > Code Terms** | New top-level domain folder OR new recurring class/component prefix introduced in the diff | Add `**Term**: one-line definition. path-pointer.` Only act when the section exists; do not auto-create it. |
   | **Glossary > Business Terms** | — | Never auto-update (human-curated) |
   | **Anti-patterns** | — | Never auto-update (human-curated) |
   | **Mission** | — | Never auto-update |

   **Self-filter** — apply to each candidate update before writing:

   1. Is it a **structural** addition (long-lived, future AI needs it to find/follow it)? → if no, skip
   2. Is it already covered by an existing entry? → if yes, skip or merge
   3. Is it project-specific? → if it's generic framework knowledge, skip
   4. Does it embed a version number outside Tech Stack? → strip the version before writing
   5. Survivors: write directly to `context.md`, no confirmation prompt

   **Write rules**:
   - Append within the relevant section (do not reorder unrelated content)
   - Preserve the user's hand-edits — never rewrite an existing line, only add or replace by exact match
   - Preserve the inline HTML guidance comments verbatim — they are load-bearing for future AI re-runs
   - Do NOT touch sections marked "Never auto-update" above
   - If `context.md` does not exist, skip this step silently (do not auto-create it — that is `/esdd-init`'s job)
   - Historical / migration rules rejected from Hard Rules go into `knowledge.md/Gotchas` in the same step (counts toward the knowledge total in the summary)

   Track the count of updated sections for the final summary.

6. **Review related knowledge (scoped)**

   If `feature-spec/knowledge.md` exists and has content:
   - Read existing entries
   - Identify entries that might be affected by this change (same domain area, same files, same features)
   - For each potentially affected entry, verify against the current codebase:
     - Does the referenced file/path/env var still exist?
     - Has the described behavior changed due to this change?
   - If outdated entries found:
     - Display them with explanation of why they appear outdated
     - Use **AskUserQuestion**: "Update / Remove / Keep as-is" for each
     - Apply confirmed changes

   **If no `feature-spec/knowledge.md` exists or no related entries:** Skip silently.

7. **Delete change artifacts**

   ```bash
   rm -rf feature-spec/changes/<name>
   ```

   After deletion, check remaining state:
   - If `feature-spec/changes/` is now empty (no more active changes):
     - Also delete `feature-spec/specs/` (main specs are no longer needed)
     - Also delete `feature-spec/changes/` directory itself
     - Delete `feature-spec/archive/` if it exists (legacy)
   - **Always keep** `feature-spec/config.yaml` and `feature-spec/context.md` — they're reused by future `/esdd-propose` and `/esdd-quick`

8. **Commit**

   Stage all changes (knowledge.md updates, context.md updates, doc updates, deleted change files):
   - Single change: `chore: complete <change-name>, extract knowledge`
   - Batch mode: `chore: complete <name1>, <name2>, ...`
   - Do NOT push to remote — only commit locally

9. **Display summary**

   **Single change:**
   ```
   ## Change Complete: <change-name>

   **Tasks:** M/M complete ✓
   **Knowledge:** N items added to knowledge.md (or "No new knowledge")
   **Context:** Synced K sections in context.md (or "No structural updates")
   **Docs:** Updated CLAUDE.md, README.md (or "No updates needed")
   **Outdated knowledge:** Removed/updated J items (or "None found")
   **Cleaned up:** feature-spec/changes/<name>/ deleted
   ```

   **Batch mode:**
   ```
   ## Batch Complete

   Completed N change(s):

   | Change | Tasks | Knowledge Added | Context Synced | Docs Updated | Cleaned Up |
   |--------|-------|----------------|---------------|--------------|------------|
   | add-user-search | 5/5 ✓ | 3 items | 2 sections | README.md | ✓ |
   | fix-login-bug | 3/3 ✓ | 0 items | — | — | ✓ |

   Skipped M change(s) with incomplete tasks:
   - refactor-auth: 2/4 tasks complete
   ```

---

## Guardrails

- Batch mode (no name provided) only completes fully finished changes — never completes incomplete ones without explicit naming
- When a name is explicitly provided, allow completing incomplete changes with user confirmation
- **Knowledge entries are pointers, not paragraphs** — one project-specific fact per bullet with a file-path pointer; never logic walkthroughs or generic advice
- **One line per entry, hard rule** — two lines only when a single fact genuinely needs both halves; if "and", "because", or multi-clause conditions appear, collapse to a pointer or split the entry
- **No speculative entries** — knowledge.md captures past pain only; drop "if future" hedges and keep only the verified fact (or drop the entry entirely)
- **Skeleton HTML comments are part of the file** — preserve the per-section guidance comments verbatim when appending; they tell future contributors what each category is for
- **`knowledge.md` is written in English**, regardless of the user's conversation language
- Apply the self-filter (project-specific? pointer vs walkthrough? collapsible?) and write surviving entries **directly to `knowledge.md`** — do NOT ask the user to pick. The user will correct after the fact; expand this skill's "Do NOT record" list over time as corrections accumulate.
- Scoped knowledge review only checks entries related to the current change, not the entire file
- **`feature-spec/context.md` sync is auto-apply** — append/replace structural sections without confirmation; never touch Mission, Anti-patterns, or Glossary > Business Terms; Glossary > Code Terms may be appended only when the section already exists; if `context.md` does not exist, skip silently (do not auto-create)
- **Hard Rules sync is classified** — structural invariants go to context.md/Hard Rules; historical or version-pinned rules go to knowledge.md/Gotchas instead, in the same sync pass
- **Domain map stays in pointer form** — never enumerate file lists during sync; pointer + cardinality only
- **Versions live only in Tech Stack & Versions** — strip version numbers from any sync candidate destined for other sections
- Always keep `feature-spec/config.yaml` and `feature-spec/context.md` — never delete them
- Show clear summary of what happened
- Never push to remote — only commit locally
