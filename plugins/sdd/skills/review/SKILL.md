---
name: review
description: >
  Use when you want a standalone, read-only review of existing code, a diff, an API/controller,
  a stored procedure, or a page — without changing anything. Also use when you have no specific
  target and want to know where the codebase is decaying ("哪裡爛了", architecture health check).
  Dispatches the matching review-family agent(s) by lens (quality / security / performance / e2e),
  auto-detecting the lens from the target when not specified. Read-only: no code edits, no commits,
  no implementation agents.
user-invocable: true
argument-hint: "[target] [quality | security | performance | e2e | all]   — omit the target for an architecture health scan"
---

Standalone review entry point. Unlike `/quick` (a **change** pipeline that dispatches implementation agents and commits), `/sdd:review` is **read-only**: it dispatches one or more review-family agents against a target you already have, collects their findings, and stops. It never edits code, never commits, and never dispatches implementation or fix agents — acting on findings is your call (use `/quick` for that).

Two entry conditions, same read-only contract:

- **You have a target** — the lens review below. Steps 1–7.
- **You have no target** — the **architecture health scan**: the codebase picks the target for you. Agents accelerate entropy as much as they accelerate features, so decay accumulates in places nobody thought to point at. See *Health scan mode*.

## Lenses

| lens | agent | reviews | not |
|---|---|---|---|
| `quality` | review-engineer | architecture compliance, code-level correctness, maintainability, patterns, over-engineering (reinvented stdlib / dead abstractions / needless deps — what to delete) | does not run tests to verify behaviour |
| `security` | security-engineer | vulnerabilities, OWASP, injection, authn/authz, secrets/config, dependency risks | does not judge performance/architecture |
| `performance` | performance-engineer | FE (CWV/bundle), BE (API/SP/query), data-scale capacity — **static, report-only** | does not run load tests/profilers; SP-internal tuning → DBA |
| `e2e` | qa-engineer | runs Playwright E2E against a spec's WHEN/THEN or supplied acceptance criteria | needs a runnable app + criteria; not for a bare SP/query |
| `all` | all four | — | — |

## Steps

0. **Detect repo topology (MANDATORY first)**

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. Announce the mode. In **multi-repo** mode, resolve the target to the child repo(s) that contain it; each review agent is bound to the repo holding its target (`git -C <repo> ...`).

1. **Resolve the target**

   Parse the first argument as the **target** — **except when it is a bare lens keyword.** If the first argument is exactly `quality` / `security` / `performance` / `e2e` / `all` and no other argument follows, the user named a lens and gave no target (`/sdd:review security`); treat this as the no-target case below and carry that lens into Step 2 as the chosen one. Do NOT resolve a lens keyword as a target — that sends Step 2's name-resolution branch hunting for a symbol called `security` and it either finds nothing or locks onto an unrelated file.

   If no target is given, use **AskUserQuestion** to offer both entry conditions — do NOT silently demand a target, and do NOT silently start scanning:
   - *"(1) 我給目標"* → open-ended follow-up: a path/glob, a diff like `HEAD~3..HEAD` or `staged`, an API/controller, or a stored-procedure name. Continue with Step 2.
   - *"(2) 架構健檢 — 你去找哪裡爛了"* → jump to *Health scan mode*; Steps 2–7 do not apply. **A lens carried in from a bare-keyword invocation is dropped here** — the health scan has no lenses, so do not invent a lens-filtered variant of it. Say so in one line when it happens (`架構健檢不分 lens，<lens> 先忽略`) rather than dropping it silently.

   Resolve the target to a concrete scope to hand each agent:
   - **path / glob** → those files
   - **`diff` / `staged` / `<base>..<head>`** → the git diff range (compute `BASE_SHA`/`HEAD_SHA`)
   - **a name** (SP, controller, endpoint, component) → `grep`/`Glob` to locate its definition **and** call sites; the scope is the definition plus the immediate callers
   - **a repo / directory** → that subtree (warn if very large; ask whether to narrow)

2. **Determine the lens(es)**

   - **Lens given explicitly** in the args (`quality` / `security` / `performance` / `e2e` / `all`) → use it; `all` selects all four.
   - **No lens given** → auto-detect candidates from the target's nature and any phrasing the user added, then **confirm via AskUserQuestion** (multiSelect) with the detected lenses **pre-selected** so the full option list is always visible:

     | target signal | pre-select |
     |---|---|
     | `.vue` / page / component / route | quality, performance |
     | API endpoint / controller / minimal-api handler | quality, security, performance |
     | stored procedure / SQL / Dapper / EF query / repository | performance, quality |
     | auth / login / token / crypto / payment / PII | security (always), + quality |
     | batch job / data pipeline / pandas / FastAPI service | performance, quality |
     | user-facing flow with a spec present | + e2e |

     Phrasing overrides signals: if the user wrote "效能 / performance / 撐不撐得住" → performance; "injection / 安全 / auth" → security; etc. Present the menu, dispatch what the user confirms.

   - **Default is NOT `all`** — pre-select only the most-implied 1–2 lenses. Running all four is opt-in (the user ticks them, or passes `all`).

3. **Ground each agent**

   For each touched repo, read `feature-spec/config.yaml` if present (forward it verbatim as `## Project Context`; `hard_rules` are binding); otherwise rely on a code scan. Each dispatched agent's prompt MUST carry the **project-knowledge directive**: state its target repo name/key and instruct it to consult any available project-knowledge skill for that repo before reviewing. Name no specific skill; skip if none matches.

4. **e2e gate (only if `e2e` is selected)**

   Before dispatching qa-engineer, check for (a) acceptance criteria — a spec under `feature-spec/specs/**` or `changes/**/specs/**` covering the target, and (b) a runnable app + Playwright setup.
   - **No criteria** → **AskUserQuestion**: *"This target has no spec. Choose: (1) I'll give the expected behaviour now (ad-hoc WHEN/THEN — real acceptance); (2) smoke + existing-regression only (labelled NOT acceptance, no correctness guarantee); (3) skip e2e."* Do NOT let qa-engineer invent the intended behaviour and validate against its own guess.
   - **No runnable env / no Playwright** → report that e2e cannot run; offer to skip and proceed with the other lenses.

5. **Dispatch the review agents (read-only, parallel)**

   Dispatch the confirmed lenses' agents **simultaneously in one message**, in the background (`run_in_background: true`, `mode: "bypassPermissions"`), each with a **stable descriptive `name`** (e.g. `review:security`, `review:perf`) and bound to its target repo and scope. Each agent's prompt MUST include:
   - The resolved target scope (file list, or `git diff BASE_SHA..HEAD_SHA`, or definition+callers)
   - `## Project Context` (config.yaml verbatim) when present + the project-knowledge directive
   - **Hard read-only constraint**: *"Review and report ONLY. Do NOT edit any file, do NOT create commits, do NOT dispatch other agents. Return findings as a structured report."*
   - performance-engineer: capacity analysis is **static**; output is a per-path verdict (SAFE / RISKY / WILL NOT SCALE). **MANDATORY for any backend/data/batch code in scope — the primary OOM defense: exhaustively enumerate every point where an external store's data is loaded into memory and give each a boundedness verdict; do NOT report only the slow-looking ones. When a path's size is unknown, emit `NEEDS:` for the row count instead of guessing a threshold.**

   **Keep them alive.** Do NOT treat reviewers as one-shot. After they report, they stay backgrounded — follow-up questions and re-reviews go back to the **same** agent via **SendMessage** (its context, loaded skills, and the files it already read are intact), which avoids re-paying agent startup. Only spawn a fresh reviewer if its context was lost or the target changed substantially.

   You ARE the dispatcher — do NOT spawn the orchestrator, and do NOT run an automatic fix loop. There is no Phase 2/auto-fix/commit here.

6. **Consolidate and report**

   Collect all agents' reports and present one consolidated review. Do NOT change code or commit.

   ```
   ## Review: <target>
   **Lenses:** <list>   **Repo(s):** <list>   **Scope:** <files / diff range / definition+callers>

   ### quality — review-engineer        [no findings / N findings]
   ### security — security-engineer      [SECURE / N findings]
   ### performance — performance-engineer [verdict table: SAFE/RISKY/WILL NOT SCALE]
   ### e2e — qa-engineer                 [PASSED / FAILED / SMOKE-ONLY / SKIPPED — no spec]

   ### Top recommendations (priority-ordered, advisory)
   - ...

   > 要追問或直接修嗎?跟我說要看哪項或改哪幾項 — 追問我問回原 reviewer,修我派對應 specialist。
   ```

7. **Follow-up & fix handoff (stay conversational)**

   The reviewers are still alive in the background and the consolidated findings are in this conversation's context. Respond to the user without re-running the whole review:

   - **Follow-up question** ("explain finding 3", "is Y affected too?", "re-check after I edited X") → **SendMessage to the same reviewer** that produced it. Do NOT spawn a fresh agent — its context is intact.

   - **A reviewer returns a `NEEDS:`** (it cannot verify a finding without an external fact — a production value, a cross-repo/service contract, live infra state): resolve it with whatever tools you have and **SendMessage the same reviewer** to finish that check (context intact); if unresolvable, surface it to the user and report the item as explicitly *unverified* — never let the reviewer guess. See `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns*.

   - **"Fix N" / "改第 2 跟第 4 個"** → **always dispatch the owning specialist** (the engineer per the routing table — vue / dotnet / python / godot / electron / database / devops), never edit the file yourself. The specialist loads its domain skills, consults project-knowledge, and matches repo conventions — the main loop has none of that, so a "small" main-loop edit risks breaking project-specific rules. Keep the specialist **backgrounded and alive** so successive fix rounds reuse it via **SendMessage** instead of re-spawning.
     - Compose the fix prompt from the relevant finding(s) + scope + `## Project Context`.
     - This is the one place `/sdd:review` produces changes — and it does so by **delegating to a specialist**, exactly like `/quick`'s fix path. (For multi-finding or cross-cutting fixes, suggest `/quick "<summary>"` instead.)

   - **Re-verify a fix** → **SendMessage the original reviewer** ("the fix landed at <sha/files>, re-check finding N"); it re-reviews with its existing context. Stay read-only on the review side.

   Reviewers and fix specialists are torn down only when the user ends the review session.

## Health scan mode (no target given)

Nobody points at the module that is quietly rotting — that is exactly why it rots. Here the codebase nominates its own targets, and the output is a **ranked shortlist of candidates to fix**, not a review of one thing.

Load the `codebase-design` skill and use its vocabulary throughout (**module / interface / depth / seam / adapter / leverage / locality**). Do not drift into "component", "service", or "boundary" — the shared language is what makes the candidates comparable to each other and to the architect later.

1. **Pick where to look — scope before you scan.** Deepening a module pays off only through *future* changes to it, so a beautiful refactor of code nobody touches returns nothing. Walk back a decent stretch of `git log --oneline --name-only` and let the **hot spots** — the files and directories that keep reappearing — pull your attention first. If the history is evenly scattered with no hot spot, widen the net and say so. Read `feature-spec/config.yaml` (`architecture`, `hard_rules`) first if present; in multi-repo mode, run this per repo and keep the results separated.

2. **Explore for friction.** Dispatch the **Explore** agent over the hot spots. Do not go down a heuristic checklist — look for where the code *resists*:
   - Understanding one concept requires bouncing between many small modules.
   - A module is **shallow** — its interface is nearly as complex as its implementation.
   - Pure functions were extracted for testability, but the real bugs live in how they are called (no **locality**).
   - Tightly-coupled modules leaking across their seams.
   - Code that is untested because it is untestable through its current interface.

3. **Apply the deletion test to every suspect.** Imagine the module deleted. Does complexity *vanish* (it was a pass-through — the candidate is to remove it) or does it *reappear across N callers* (it was earning its keep — leave it alone)? A "yes, concentrates" is the signal worth reporting; anything failing this test is noise and does not go in the table.

4. **Report candidates, ranked.** Do not propose interfaces yet — this step surfaces *what* is worth fixing, not *how*.

   ```
   ## 架構健檢: <repo> — 掃描範圍 <hot spots / 全域> · commits <range>

   | # | 模組 / 檔案 | 現在的摩擦 | 改成 | 收益 (leverage / locality) | 強度 |
   |---|---|---|---|---|---|

   ### 最建議先動: #N — <one line why this one first>
   ```

   `強度` is `Strong` / `Worth exploring` / `Speculative`. Where a candidate contradicts an existing `design.md` decision or a `hard_rule`, surface it **only** if the friction is real enough to justify reopening that decision, and mark it `⚠ 與 <decision> 相衝 — 但值得重開，因為…`. Do not list every refactor a rule forbids.

5. **Hand off — do not start fixing.** Ask which candidate the user wants to pursue. A chosen candidate is an *idea*, not a change: send it to `/propose` (or `/quick` if genuinely small), where the interface actually gets designed. Health scan mode stays read-only like the rest of this skill — no edits, no commits, no implementation agents.

## Guardrails

- **Review side is read-only** — reviewers never edit, commit, change branches, or dispatch other agents. Fixes happen ONLY when the user explicitly asks, and ONLY by **dispatching the owning specialist** — the main loop never hand-edits code (no specialist skills / project grounding loaded). This delegation is what keeps `/sdd:review` consistent with sdd's "never self-implement, even trivial" rule.
- **No automatic fix loop** — unlike `/quick`/`/apply`, there is no auto fix→re-review→commit cycle. Fixes are user-driven, one ask at a time, and `/sdd:review` never commits.
- **Reuse agents via SendMessage, don't re-spawn** — reviewers and fix specialists are backgrounded and kept alive; follow-ups and re-reviews continue the same agent (context intact) to avoid startup cost. Spawn fresh only on lost context or a substantially changed target.
- **You ARE the dispatcher** — do NOT spawn a separate orchestrator agent.
- **Default lens is the most-implied 1–2, never silently `all`** — running every lens is opt-in.
- **No target ⇒ ask, never assume** — offer both the give-me-a-target path and the health scan; do not demand a target, and do not start scanning uninvited. Health scan mode ends at a ranked candidate list handed to `/propose` — it never designs the fix or edits code.
- **e2e never guesses intended behaviour** — no spec ⇒ ask (criteria / smoke-only / skip), and label smoke runs as non-acceptance.
- `feature-spec/config.yaml` (when present) is forwarded verbatim as `## Project Context`; `hard_rules` are binding. The project's own prose docs are never read or forwarded.
- **Language**: all output in Traditional Chinese; code and comments in English.
