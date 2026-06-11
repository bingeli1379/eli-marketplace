---
name: review
description: >
  Use when you want a standalone, read-only review of existing code, a diff, an API/controller,
  a stored procedure, or a page — without changing anything. Dispatches the matching review-family
  agent(s) by lens (quality / security / performance / e2e), auto-detecting the lens from the target
  when not specified. Read-only: no code edits, no commits, no implementation agents.
user-invocable: true
argument-hint: "<target> [quality | security | performance | e2e | all]"
---

Standalone review entry point. Unlike `/quick` (a **change** pipeline that dispatches implementation agents and commits), `/sdd:review` is **read-only**: it dispatches one or more review-family agents against a target you already have, collects their findings, and stops. It never edits code, never commits, and never dispatches implementation or fix agents — acting on findings is your call (use `/quick` for that).

## Lenses

| lens | agent | reviews | not |
|---|---|---|---|
| `quality` | review-engineer | architecture compliance, code-level correctness, maintainability, patterns | does not run tests to verify behaviour |
| `security` | security-engineer | vulnerabilities, OWASP, injection, authn/authz, secrets/config, dependency risks | does not judge performance/architecture |
| `performance` | performance-engineer | FE (CWV/bundle), BE (API/SP/query), data-scale capacity — **static, report-only** | does not run load tests/profilers; SP-internal tuning → DBA |
| `e2e` | qa-engineer | runs Playwright E2E against a spec's WHEN/THEN or supplied acceptance criteria | needs a runnable app + criteria; not for a bare SP/query |
| `all` | all four | — | — |

## Steps

0. **Detect repo topology (MANDATORY first)**

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. Announce the mode. In **multi-repo** mode, resolve the target to the child repo(s) that contain it; each review agent is bound to the repo holding its target (`git -C <repo> ...`).

1. **Resolve the target**

   Parse the first argument as the **target**. If none is given, use **AskUserQuestion** (open-ended): *"What do you want reviewed? (a path/glob, a diff like `HEAD~3..HEAD` or `staged`, an API/controller, or a stored-procedure name)"*. Do NOT proceed without a target.

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
   - performance-engineer: reminder that capacity analysis is **static** and the output is a per-path verdict (SAFE / RISKY / WILL NOT SCALE)

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

   - **"Fix N" / "改第 2 跟第 4 個"** → **always dispatch the owning specialist** (vue / dotnet / python / database engineer), never edit the file yourself. The specialist loads its domain skills, consults project-knowledge, and matches repo conventions — the main loop has none of that, so a "small" main-loop edit risks breaking project-specific rules. Keep the specialist **backgrounded and alive** so successive fix rounds reuse it via **SendMessage** instead of re-spawning.
     - Compose the fix prompt from the relevant finding(s) + scope + `## Project Context`.
     - This is the one place `/sdd:review` produces changes — and it does so by **delegating to a specialist**, exactly like `/quick`'s fix path. (For multi-finding or cross-cutting fixes, suggest `/quick "<summary>"` instead.)

   - **Re-verify a fix** → **SendMessage the original reviewer** ("the fix landed at <sha/files>, re-check finding N"); it re-reviews with its existing context. Stay read-only on the review side.

   Reviewers and fix specialists are torn down only when the user ends the review session.

## Guardrails

- **Review side is read-only** — reviewers never edit, commit, change branches, or dispatch other agents. Fixes happen ONLY when the user explicitly asks, and ONLY by **dispatching the owning specialist** — the main loop never hand-edits code (no specialist skills / project grounding loaded). This delegation is what keeps `/sdd:review` consistent with sdd's "never self-implement, even trivial" rule.
- **No automatic fix loop** — unlike `/quick`/`/apply`, there is no auto fix→re-review→commit cycle. Fixes are user-driven, one ask at a time, and `/sdd:review` never commits.
- **Reuse agents via SendMessage, don't re-spawn** — reviewers and fix specialists are backgrounded and kept alive; follow-ups and re-reviews continue the same agent (context intact) to avoid startup cost. Spawn fresh only on lost context or a substantially changed target.
- **You ARE the dispatcher** — do NOT spawn a separate orchestrator agent.
- **Default lens is the most-implied 1–2, never silently `all`** — running every lens is opt-in.
- **e2e never guesses intended behaviour** — no spec ⇒ ask (criteria / smoke-only / skip), and label smoke runs as non-acceptance.
- `feature-spec/config.yaml` (when present) is forwarded verbatim as `## Project Context`; `hard_rules` are binding. The project's own prose docs are never read or forwarded.
- **Language**: all output in Traditional Chinese; code and comments in English.
