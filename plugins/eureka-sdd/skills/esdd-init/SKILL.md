---
name: esdd-init
description: >
  Initialize feature-spec directory structure and auto-generate config.yaml +
  context.md with project context. Two-phase: SCAN (dry-run + confirm) then
  BUILD (write files). Use when setting up a new project for the eureka-sdd,
  or when the user wants to reconfigure project context.
user-invocable: true
---

Initialize the `feature-spec/` directory in the current project. Auto-generates up to three artifacts:

- `feature-spec/config.yaml` — tool-runnable config (lint/verification commands, rules)
- `feature-spec/context.md` — AI-readable project context (architecture layers, domain map, entry points, conditional subsystems, hard rules, anti-patterns, glossary, common commands) so AI knows **where to make changes**
- `feature-spec/knowledge.md` — annotated skeleton harvested from `.env.example` (env vars with non-obvious behavior), informational code comments (`// note:`, `// because:`, `// only X when Y`), and **named-symbol historical rules** from `CLAUDE.md` / `AGENTS.md` (only kept when the rule names a code symbol that still resolves in the codebase). Hard cap of 5 candidates per init. When an existing file with real entries is present, an inline audit pass re-verifies every entry's `path:line` citation and surfaces stale / outdated / uncited entries for user decision.

Runs in two phases: **SCAN** (analyze + confirm) then **BUILD** (write files). No arguments required.

---

## Reference layout (load on demand)

Detailed rules live in `references/`. Load only what each phase needs:

| When | Load |
|---|---|
| Phase 1 steps 1–3 (auto-detect tech stack / lint / context.md sections) | `references/detection-rules.md` |
| Phase 1 step 4 (knowledge.md seed candidates) | `references/knowledge-seed.md` |
| Phase 1 step 4.5 (existing-entry audit, **only when knowledge.md has real content**) | `references/audit.md` |
| Phase 2 (BUILD: write `config.yaml` / `context.md` / `knowledge.md`) | `references/write-rules.md` |

The main file (this one) holds the flow, the SCAN-report contract, the question rules, and the skill-wide guardrails.

---

## Phase 0 — Pre-flight

1. **Inventory existing artifacts**
   - If `feature-spec/` does not exist → SCAN will create everything.
   - Otherwise check each: `config.yaml`, `context.md`, `knowledge.md`, subdirs `specs/`, `changes/`.
   - For each existing artifact, use **AskUserQuestion** to choose: "Regenerate (overwrite)" or "Keep existing".
   - **`knowledge.md` special case**: regardless of "keep" vs "regenerate", if the file exists with real entries (more than skeleton + HTML comments), Phase 1 step 4.5 runs an inline audit and surfaces findings in the SCAN report. "Regenerate" still wipes the file at BUILD time; "Keep existing" preserves the file but lets the user act on audit findings via the audit-decision batch question.
   - Always create missing subdirectories:

   ```bash
   mkdir -p feature-spec/specs feature-spec/changes
   ```

2. **Migrate legacy `./knowledge.md` → `feature-spec/knowledge.md` (silent, one-time)**

   Earlier versions of this plugin wrote `knowledge.md` to the project root. Migrate without asking:
   - Source-only exists → `git mv knowledge.md feature-spec/knowledge.md` (fall back to `mv` if untracked). Announce: `Moved knowledge.md → feature-spec/knowledge.md (legacy location migration)`.
   - Both exist → leave both. Surface BUILD-time warning: `⚠️ ./knowledge.md and feature-spec/knowledge.md both exist — please reconcile manually.`
   - Migration is silent because the move is reversible and content is preserved.

---

## Phase 1 — SCAN (dry-run, no files written)

**No files written in this phase.** Phase 1 execution order: 1 → 2 → 3 → 4 (raw candidates, defer dedup) → 4.5 → dedup → 5.

### 1. Auto-detect tech stack

Load `references/detection-rules.md` § 1 and follow it.

### 2. Auto-detect lint and verification commands

Load `references/detection-rules.md` § 2 and follow it.

### 3. Auto-detect context.md content

Load `references/detection-rules.md` § 3 and follow it. Tag each section's confidence using the 4-level scale defined in `detection-rules.md § Confidence tagging`: ✅ High / ⚠️ Medium / ○ N/A (inapplicable to this repo type) / ❌ Low (signal should exist but missing — only this triggers a question).

### 4. Collect knowledge.md seed candidates (file scan only — no git mining)

Load `references/knowledge-seed.md` and run its sources + filter passes (Cite-or-Skip → self-skeptic → counter-example). Surviving candidates feed the SCAN report.

### 4.5. Audit existing `knowledge.md` entries (only when file has real content)

**Skip entirely** when any of the following is true:
- `feature-spec/knowledge.md` does not exist.
- The file contains only the canonical skeleton (headings + HTML guidance comments + zero real entries).
- The user picked "Regenerate (overwrite)" for `knowledge.md` in Phase 0 (file will be wiped anyway).

Otherwise load `references/audit.md` and run its per-entry pipeline. Output feeds the SCAN report's "既有 knowledge.md 審計" section.

**Dedup new candidates against audited entries** (run after step 4.5 finishes, before step 5 renders the report): take the `✅ Still valid` and `⚠️ Needs rewrite` entries from step 4.5 and use them to filter the raw candidate list collected by step 4. Drop any new candidate whose claim semantically overlaps an audited entry (same `path:line` neighborhood + same direction of claim).

### 5. Present scan report and ask up to 3 confirmation questions

Output the scan report in **Traditional Chinese** to the conversation. Use compact table form so the user can scan everything in one screen — never expand into multi-line bullet lists with prose. Format:

```
## SCAN Report

### 偵測結果
（圖示：✅ 高信心 / ⚠️ 中信心，建議檢視 / ❌ 低信心，將問你 / ○ 不適用，不寫入）

| | Section        | Detected |
|---|----------------|----------|
| ✅ | Tech stack     | <lang · framework · build · pkg manager 全部濃縮成一行> |
| ✅ | Lint           | <commands joined with ` · `> |
| ✅ | Verification   | <commands joined with ` · `> |
| ✅ | Entry points   | <N dirs: dir1 · dir2 · dir3 · ...> |
| ✅ | Common cmds    | <N scripts in package.json> |
| ⚠️ | Mission        | "<one-line guess>" |
| ⚠️ | Architecture   | <layers + style summary, one line> |
| ⚠️ | Domain map     | <N domains under <path>/: name1 · name2 · ...> |
| ⚠️ | Cross-cutting  | <N concerns: name1 · name2 · ...> |
| ⚠️ | Hard rules     | <count> structural invariants from <source> |
| ❌ | Glossary       | <"omitted (reason)" or "N code / M business terms (待你補)"> |
| ○ | Conditional    | none detected |
| ○ | Anti-patterns  | omitted (no examples) |

注：表格不可拆成多行。每 section 一行，超過螢幕寬度寧可用 `·` 分隔短名稱也不要換行。

### 既有 knowledge.md 審計  ✅ <X> 仍有效 · ⚠️ <Y> 改寫 · ❌ <Z> 失效 · ❓ <W> 無 citation　（共 N 條）
（僅當步驟 4.5 有跑時顯示。整個 section 在步驟 4.5 被跳過時連同標題一起省略。✅ 不逐條列。）

A1  ⚠️ 建議改寫
    原文: <既有條目原文>
    📍 path:line  (resolves)
    Issue: <one-line drift description in Chinese>
    Suggested: <new one-line claim — file content stays in English>

A2  ❌ Citation 失效
    原文: <既有條目原文>
    📍 path:line  (檔案缺失 / 行號超出範圍)

A3  ❓ 無 citation
    原文: <既有條目原文>
    （請手動審視）

### Knowledge seed candidates　共 <N> 條（上限 5；預設未答 = `none`）
（內容空時整個 section 連同標題一起省略並跳過 candidate-selection question。）

C1  [Dev Environment]  <one-line claim>
    📍 path:line
    ```<lang>
    <3-5 line snippet>
    ```

C2  [Gotchas] ⚠️ Name-vs-impl mismatch
    <one-line claim>
    📍 path:line
    ```<lang>
    <3-5 line snippet>
    ```

### 將寫入
- feature-spec/config.yaml      <new | overwrite | keep>
- feature-spec/context.md       <new | overwrite | keep>
- feature-spec/knowledge.md     <new skeleton | existing — audit + append | keep>

### 待確認（預設 0 題；上限 3 題，僅 ❌ Low-confidence sections）
<列出將透過 AskUserQuestion 詢問的題目，每題一行。零題時寫 `無，將直接 BUILD（按 Ctrl+C 取消）`。⚠️ Medium 不問，trust the draft。>
```

**Format guardrails for the SCAN report**:
- One line per section in the 偵測結果 table — never expand into bullet sub-lists or prose.
- Use `·` (middle dot) as the list separator inside a single cell. Avoid commas and `/` because they get visually noisy when many items appear.
- Confidence icons are tags, not section names — keep the section name in the second column verbatim.
- The ✅/⚠️/❌/○ legend appears once below the heading. Do not repeat per section.
- 既有 knowledge.md 審計 summary line uses the same `· ` separator. Skip the whole section when step 4.5 was skipped.
- Candidate snippets stay 3–5 lines max. If the surrounding code needs more context to make sense, the candidate is too complex — drop it.
- 將寫入 list always shows action labels (`new` / `overwrite` / `keep` / `existing — audit + append`). Never leave action ambiguous.
- 待確認 list shows only the actual questions about to be asked — not all medium-confidence sections. If gap-filling skips a section, that section does not appear here.

#### Gap-filling questions (Low-confidence only; default 0 questions)

Default behavior: **ask nothing**. If every section came out ✅ High or ⚠️ Medium confidence, the user gets the SCAN report and BUILD runs straight after — they can edit the file by hand if any draft was off. Medium = "AI thinks it's right" → trust the draft, do not nag.

Only when a section is **❌ Low confidence** (AI literally could not infer) does it become a question candidate. Cap remains 3 — more than 3 Low-confidence sections means the project has too little signal to auto-init; let the user fill in by hand.

Question candidates (asked only when the matching condition is true):

1. **Mission** — `README` missing entirely OR README is meta-only (no project description):
   "What does this project do, in one sentence?"
2. **Domain-to-Code Map** — only one top-level dir under `src/` / `app/` (cannot distinguish multiple domains):
   "I see only `<dir>/` — what are the top-level domains in this project?"
3. **Hard Rules** — no `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md`, or custom `eslint.config.*` rules at all:
   "Any architectural rules AI must not break? (e.g., 'Endpoints don't access DbContext directly') — leave blank to skip"

Each question must include a default suggested answer (when one can be inferred) + a "Skip / use my draft as-is" option.

**SCAN report rendering when zero questions**: the `### 待確認` section shows `無，將直接 BUILD（按 Ctrl+C 取消）`. Do not invent fake questions to fill the section.

#### Audit-decision question (separate from the 3-cap)

Asked only when step 4.5 ran with at least one ⚠️ / ❌ / ❓ finding. See `references/audit.md` § "Audit-decision question" for the exact prompt. Skip when step 4.5 was skipped or produced zero findings.

#### Candidate-selection question (separate from the 3-cap)

Asked only when step 4 produced one or more surviving candidates. Use `AskUserQuestion`. Three layouts depending on candidate count (cap is 5; AskUserQuestion's `options.minItems` is 2 so N=1 cannot use multiSelect):

**When N = 1 → single-select Apply / Skip**:

```
AskUserQuestion({
  questions: [{
    question: "Knowledge seed candidate — append?",
    header: "Candidate",
    multiSelect: false,
    options: [
      { label: "Skip (Recommended)", description: "False knowledge is worse than missing knowledge" },
      { label: "Append C1",          description: "<C1 claim shortened> · <category> · <path:line>" }
    ]
  }]
})
```

`Append C1` → write the candidate. Anything else (Skip / dismissed / Other) → write nothing.

**When 2 ≤ N ≤ 4 → multiSelect (one option per candidate)**:

```
AskUserQuestion({
  questions: [{
    question: "Knowledge seed candidates — which to append? (default: 不勾 = none)",
    header: "Candidates",
    multiSelect: true,
    options: [
      { label: "C1: <claim shortened to ~50 chars>", description: "<category> · <path:line>" },
      { label: "C2: ...",                            description: "..." },
      // up to 4 options
    ]
  }]
})
```

User checks the candidates to keep. Empty selection / dismissed → write nothing.

**When N = 5 candidates → mode-based (cannot fit 5 options)**:

```
AskUserQuestion({
  questions: [{
    question: "5 knowledge seed candidates — keep which?",
    header: "Candidates",
    multiSelect: false,
    options: [
      { label: "None (Recommended)", description: "False knowledge is worse than missing knowledge" },
      { label: "Keep all 5",         description: "Append every candidate under its category heading" },
      { label: "Pick specific",      description: "Reply in Other with C-prefix indices (e.g. C1,C3,C5)" }
    ]
  }]
})
```

`Pick specific` parses Other free-text for C-prefix indices. Empty / unparseable → fall back to `None`.

Skip the question entirely when zero candidates survived.

---

## Phase 2 — BUILD (write files based on confirmed answers)

Load `references/write-rules.md` and follow it. Steps:

1. Write `feature-spec/config.yaml` (template at `templates/config.yaml`).
2. Write `feature-spec/context.md` (template at `templates/context.md`). **Mandatory self-audit pass** before writing — see write-rules.md § "Self-audit pass".
3. Write `feature-spec/knowledge.md`:
   - Skeleton (when missing) — copied verbatim from `plugins/eureka-sdd/templates/knowledge.md`.
   - Apply audit decisions in place (whenever step 4.5 ran — even when the user dismissed the audit-decision question, the default "全部保留" still runs to inject the summary comment) — see `references/audit.md` § "Apply audit decisions".
   - Append confirmed candidates under category headings — section-fit check is mandatory.
4. Show summary — template in `references/write-rules.md` § 4.

---

## Guardrails

- **Language**: all conversation output (SCAN report, AskUserQuestion text, status announcements, BUILD summary, error messages) MUST be in **Traditional Chinese**. File contents (`config.yaml`, `context.md`, `knowledge.md`, all HTML comments, all examples) stay in **English** so they remain readable for AI agents and code reviewers downstream.
- **Two-phase is mandatory**: never skip SCAN — `context.md` has many sections and AI cannot reach >80% accuracy on all of them, so without confirmation half the file is wrong.
- **Default 0 gap-filling questions; cap 3**: only ask for ❌ Low-confidence sections (AI could not infer at all). ⚠️ Medium sections trust the draft — user can edit the file by hand. More than 3 Low-confidence sections means the project has too little signal; stop asking and let the user complete by hand.
- **Never overwrite without asking**: Phase 0 always asks per-artifact before BUILD writes.
- **Always create missing subdirectories** (`specs/`, `changes/`) even if `feature-spec/` partially exists.
- **`context.md` is markdown by design**: the format stays loose so humans edit it naturally and `/esdd-complete` can append without schema constraints.
- **Versions live in ONE place**: Tech Stack & Versions is the single source of truth. Before writing, scan the drafted `context.md` for version-number patterns (`\d+\.\d+`, `v\d+`, ISO years) outside that section and strip them — replace with the framework name or "current major".
- **Conditional sections are conditional**: omit Conditional Subsystems / Anti-patterns / Glossary entirely when not applicable; do not leave empty stubs or "TBD" placeholders.
- **Hard Rules vs knowledge.md/Gotchas**: Hard Rules are structural invariants only. Historical rules ("do not use the old X", migration leftovers) go through the **named-symbol gate** in `references/knowledge-seed.md`: only when the rule names a code symbol in backticks AND that symbol still resolves in the codebase does it become a candidate (citation = symbol's definition site). Vague historical rules and rules whose symbol no longer exists are silently dropped. The BUILD summary surfaces a `Skipped N historical rules (no resolvable symbol)` count so the user knows to review manually.
- **Domain map uses pointer form**: never enumerate component lists; rely on the path + cardinality so the doc does not rot.
- **Entry Points scan is exhaustive**: walk the full Phase 1 checklist (HTTP, pages, middleware, plugins, modules, jobs, event handlers, CLI). Missing one entry point silently breaks AI's ability to add features there.
- **Candidates require explicit user approval before writing**: `/esdd-init` shows surviving candidates inline in the SCAN report (numbered list with `path:line` + snippet, using `C`-prefix indices). Confirmation uses `AskUserQuestion` with three layouts (AskUserQuestion `options.minItems = 2`): single-select Apply/Skip when N=1, multiSelect checkboxes when 2 ≤ N ≤ 4, mode-based options (`None` / `Keep all` / `Pick specific`) when N=5. Only entries the user explicitly selects (or all when "Keep all" picked) are appended to `knowledge.md`. Default if dismissed = nothing written (false knowledge worse than missing). No `.draft` file is produced.
- **Candidate-selection question is exempt from the 3-cap**: the gap-filling cap (max 3 questions for Mission / Domain map / Hard Rules) does not include the candidate-selection question; they are different decision categories.
- **Existing-entry audit (step 4.5) only runs when there is real content to audit**: skip when `knowledge.md` is missing, contains only the skeleton, or the user picked "Regenerate" for it in Phase 0. AI never auto-deletes existing entries — every drop / rewrite must be approved through the audit-decision batch question.
- **Audit decisions default to "全部保留"**: when the user dismisses the audit-decision question, leave existing entries untouched and inject a single dated audit-summary HTML comment at the top of the file. Never silently apply suggested rewrites or deletions.
- **Audit-decision question is exempt from the 3-cap**: same rationale as the candidate-selection question — different decision category, asked at most once per init run, only when step 4.5 produced ⚠️ / ❌ / ❓ findings.
- **Audit + candidate dedup**: candidate scanning (step 4) must filter out anything that semantically duplicates a `✅ Still valid` or `⚠️ Needs rewrite` audited entry, so the user does not decide on the same fact twice.
- **Audit indices use prefixes**: existing audited entries in the SCAN report use `A`-prefix indices (`A1`, `A2`); new candidates use `C`-prefix indices (`C1`, `C2`). The two question replies parse independently.
- **One line per knowledge entry**: every claim appended to `knowledge.md` is exactly one line; the verification snippet shown during SCAN is dropped on write. No speculative ("if future X, then Y") claims.
- **Cite-or-Skip is non-negotiable**: every knowledge candidate must carry a `path:line-line` citation and a 3–5 line snippet. No citation → silent drop, even if the candidate "looks right". Naming alone never qualifies.
- **Citations must be code, not markdown**: `knowledge.md` entries cite `.ts` / `.cs` / `.vue` / `.py` / config files — never other markdown docs (`CLAUDE.md`, `AGENTS.md`, `README.md`). Markdown citations create circular references and are silently dropped.
- **Pointer-over-enumeration is a global context.md rule, not just Domain Map**: every section must use pointer form when listing ≥4 named items. Cross-cutting Concerns, Architecture Layers, Conditional Subsystems all fall under this rule. Entry Points is the one exception (its purpose IS to enumerate locations) — but each row inside it still points at a directory, not the handlers within.
- **context.md self-audit before write is mandatory**: AI must scan its own draft for enumeration smells (comma-lists, bullet explosions, identifier-suffix runs), version drift outside Tech Stack, and cross-doc rationale references — and rewrite hits as pointers — before persisting `context.md`. The Editing rules embedded at the top of `context.md` apply to AI at write time, not just to humans editing it later.
- **Section-fit check before knowledge.md append**: every entry's claim must match its target heading's HTML guidance comment. Common misfits (Redis host into External Dependencies, build config into Gotchas) must be re-classified or surfaced as a warning in the BUILD summary — never force-fit silently.
- **Self-skeptic + counter-example passes are mandatory**: every surviving candidate must be re-checked against the cited snippet AND grep-tested for contradicting cases before being shown in the SCAN report for user selection. Mark name-vs-impl mismatches with `⚠️` so the user can spot them at confirmation time.
- **Knowledge seed scope is intentionally narrow**: scan **only** `.env.example`, informational code comments (`// note:`, `// because:`, `// only X when Y`), and **named-symbol historical rules** from `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` (gated — symbol must resolve in code). Do NOT scan READMEs / docs / package.json scripts / git log / `HACK`/`FIXME`/`XXX` / vague rules without a code symbol — too noisy, all moved to "user adds manually if needed" + `/esdd-complete`. **Hard cap 5 candidates per init**, plus a sub-cap of 3 for historical-rule candidates.
- **Downstream compatibility**: `/esdd-propose` and `/esdd-apply` continue to read `config.yaml`. The `context:` string in `config.yaml` should at minimum point to `context.md` so agents can drill in when needed.
