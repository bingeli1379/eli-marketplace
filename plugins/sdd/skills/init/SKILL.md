---
name: init
description: >
  Initialize feature-spec directory and auto-generate config.yaml — a one-time
  baseline of tool commands plus a pointer-form architecture map. Two-phase:
  SCAN (dry-run + confirm) then BUILD (write file). Use when setting up a new
  project for sdd, or when the user wants to regenerate the config baseline.
user-invocable: true
---

Initialize the `feature-spec/` directory in the current project. Generates exactly one artifact:

- `feature-spec/config.yaml` — tool-runnable config (lint/verification commands) **plus** a pointer-form architecture baseline (tech stack, pattern, layers, entry points, hard rules).

This skill does **not** generate or maintain prose docs, and the workflow does **not** read the project's own docs (CLAUDE.md, README, `docs/`). `config.yaml` is the single, authoritative description of the project that `/propose`, `/apply`, and `/quick` consume — what AI knows is exactly what lives there. The architecture block is a one-time snapshot — it is never auto-synced. When it drifts, the user edits it by hand or re-runs `/init`.

Runs in two phases: **SCAN** (analyze + confirm) then **BUILD** (write file). No arguments required.

---

## Reference layout (load on demand)

| When | Load |
|---|---|
| Phase 1 (auto-detect tech stack / lint / verification / architecture) | `references/detection-rules.md` |
| Phase 2 (BUILD: write `config.yaml`) | `references/write-rules.md` |

This file holds the flow, the SCAN-report contract, the question rules, and the guardrails.

---

## Phase 0 — Pre-flight

0. **`/init` is per-project — guard against a multi-repo root**

   Run the topology detection from `plugins/sdd/references/repo-topology.md` § Step 0. If the result is **multi-repo** (cwd is not a git repo but contains child repos), `/init` does not apply at this level — config.yaml describes one project, not a collection. Tell the user: "`/init` runs per project. `cd` into the specific repo you want a config for and run it there. At a multi-repo root you don't need `/init` — `/propose` reads each touched repo's config if present, or scans its code." Then stop. Proceed only in **single-repo** mode (cwd inside a git repo) or a plain single-project folder.

1. **Inventory existing artifacts**
   - If `feature-spec/` does not exist → SCAN will create everything.
   - Otherwise check `config.yaml` and subdirs `specs/`, `changes/`.
   - If `config.yaml` exists, use **AskUserQuestion** to choose: `重新產生（覆寫）` or `保留現有`.
   - Always create missing subdirectories:

   ```bash
   mkdir -p feature-spec/specs feature-spec/changes
   ```

2. **Legacy artifacts (leave alone)**

   Earlier versions of this plugin generated `feature-spec/context.md` and `feature-spec/knowledge.md` (and an older `./knowledge.md` at the project root). These are no longer produced or read. Do **not** delete them — they may be files the user now keeps by hand. Just ignore them; do not reference them anywhere.

---

## Phase 1 — SCAN (dry-run, no file written)

**No file written in this phase.**

### 1. Auto-detect tech stack

Load `references/detection-rules.md` § 1 and follow it.

### 2. Auto-detect lint and verification commands

Load `references/detection-rules.md` § 2 and follow it.

### 3. Auto-detect architecture baseline

Load `references/detection-rules.md` § 3 and follow it. Detect only the fields that go into `config.yaml`: `pattern`, `layers`, `entry_points`, `hard_rules`. Tag each with the 4-level confidence scale defined in `detection-rules.md § Confidence tagging`: ✅ High / ⚠️ Medium / ○ N/A / ❌ Low (only ❌ triggers a question).

### 4. Present scan report and ask up to 3 confirmation questions

Output the scan report in **Traditional Chinese**. Goal: user scans it in one screen. **Hide ✅ High-confidence rows by default** — collapse to a one-line summary. Surface only ⚠️ Medium and ❌ Low items individually.

```
## SCAN Report

✅ <count> 項已偵測（Tech stack · Lint · Verification — 全部高信心，省略明細）

⚠️ 看一眼（中信心，OK 可不動）：
  Pattern        "<one-line guess>"
  Layers         <N: name → path · ...>
  Entry points   <N: kind → path · ...>
  Hard rules     <count> from <source>

❌ 需要你補（低信心，會問你）：
  Pattern        <reason>

○ 不適用：<list>

### 將寫入
- feature-spec/config.yaml     <new | overwrite | keep>

### 待確認（預設 0 題；上限 3 題，僅 ❌ 低信心欄位）
<每題一行。零題時寫 `無，將直接 BUILD（按 Ctrl+C 取消）`>
```

**Format guardrails:**
- ✅ rows collapse to one summary line — never list individually.
- ⚠️ / ❌ rows each get one line; use `·` as the in-line separator.
- Total report under 20 lines.

#### Gap-filling questions (Low-confidence only; default 0)

Default: **ask nothing**. Only a **❌ Low** field (AI literally could not infer) becomes a question. Cap 3. All `question` text and option labels in Traditional Chinese. Each question includes a default suggested answer + a `略過 / 使用草稿` option.

Question candidates (asked only when the matching condition is true):

1. **Pattern** — top-level layout matches no known architecture pattern:
   "這個專案用什麼架構模式？（例：Clean Architecture、MVC、Atomic Design）— 留空跳過"
2. **Entry points** — no conventional entry locations resolve and no non-standard kind matched:
   "功能主要從哪裡加進去？（例：`src/Api/` controllers、`app/pages/`）— 留空跳過"
3. **Hard rules** — no `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` / custom lint rules at all:
   "有哪些架構規則 AI 不能違反？（例：『Endpoint 不可直接存取 DbContext』）— 留空跳過"

**Zero-question rendering**: `### 待確認` shows `無，將直接 BUILD（按 Ctrl+C 取消）`. Never invent fake questions.

---

## Phase 2 — BUILD (write config.yaml)

Load `references/write-rules.md` and follow it. Write `feature-spec/config.yaml` from the template at `templates/config.yaml`, filling in `tech_stack`, `architecture` (pattern / layers / entry_points / hard_rules), `lint_commands`, `verification_commands`, and `rules` (only if project-specific rules detected). Then show the summary.

---

## Guardrails

- **One artifact only**: `/init` writes `feature-spec/config.yaml` and nothing else. It never generates `context.md`, `knowledge.md`, or any prose doc — those are the project's own responsibility.
- **Language**: all conversation output (SCAN report, AskUserQuestion text, BUILD summary, errors) in **Traditional Chinese**. File content (`config.yaml` values, comments) stays in **English** so downstream AI agents read it consistently.
- **Two-phase is mandatory**: never skip SCAN — architecture inference (pattern / layers / entry points) is not 100% accurate, so the user confirms before write.
- **Default 0 gap-filling questions; cap 3**: only ask for ❌ Low-confidence fields (AI could not infer at all). ⚠️ Medium trusts the draft — the user edits config.yaml by hand if it is off. More than 3 Low fields means the project has too little signal; stop asking and let the user fill in.
- **Never overwrite without asking**: Phase 0 asks before BUILD writes over an existing `config.yaml`.
- **Always create missing subdirectories** (`specs/`, `changes/`) even if `feature-spec/` partially exists.
- **Architecture block is pointer-form and stable**: `layers` / `entry_points` use `name → path` pointers, never file lists. `hard_rules` are structural invariants only (true a year from now) — drop lint-enforceable rules and historical/version-pinned ones. The block is a snapshot, not a living map; it is never auto-synced.
- **Versions live in `tech_stack` only**: do not embed version numbers in `architecture` or `rules`.
- **Do not read or reference the project's own docs**: `hard_rules` detection may read `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` **once** to extract structural invariants into config (vetted through SCAN), but `config.yaml` never points at those docs and the workflow never reads them again. config.yaml is the sole grounding source.
- **Entry-point scan is exhaustive**: walk the full checklist (HTTP, pages, middleware, plugins, modules, jobs, event handlers, CLI). For non-standard repos (plugin marketplace, VS Code extension, GitHub Action) list the repo's own entry convention instead — see `detection-rules.md`.
- **Downstream contract**: `/propose`, `/apply`, and `/quick` read `config.yaml` as their ONLY grounding source — the `architecture` block is all the project context an agent gets. Keep it accurate enough to orient an agent that has nothing else.
