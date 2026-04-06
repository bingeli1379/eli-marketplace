---
name: scope-contract
description: >
  Confirm a change's intent with the user as a single 現在 → 改成 (Before → After) list
  BEFORE writing any code or design. The highest-ROI gate in the sdd workflow: it catches
  the missed-downstream-consumer class of bug (a callsite not updated, a flow step
  unaccounted for) that otherwise only surfaces at review. Use standalone before a native
  coding session, inside /quick, or as the propose checkpoint. Lightweight — one chat
  message, one correction round, no artifacts.
user-invocable: true
---

Produce a **Scope Contract** for a change and show it back to the user as a regular chat message (NOT AskUserQuestion — this is a final sanity check, not an open clarification round), then wait for their reply. This is the cheapest place to catch an interpretation mismatch: a wrong contract costs 10 seconds to correct here; a wrong implementation costs minutes-to-hours to unwind.

**Prerequisite — you must already understand the change.** Before composing the contract, scan the affected code enough to know every area the change touches and trace its ripples. If you have not done that scan yet, do it first (or run it as part of `/propose` / `/quick`, which call this gate after their codebase scan). A contract built on a shallow read just relocates the guess.

## The contract

```
## 確認一下（每處 現在 → 改成，不對就講哪條，OK 就 go）

<change-name>

### 變更（現在 → 改成）

- <區域 / 行為 1>：現在 <how it works now> → 改成 <how it works after>      ← 單跳 / 大量取代：一行
- <區域 / 行為 2>：現在 ... → 改成 ...

<只有「真正改到幾條執行路徑」的變動才展開成完整行為鏈：>

**【<關鍵流程名>】**
- 現在：A → B → C
- 改成：A → B′ → C′（標出差異）

### 鎖定假設
- <假設 1>
- <假設 2>

### 不做：<one line; 省略 if 無>
### 影響範圍 / Reversibility：<one line; 省略 if "無">
```

## Depth scales with the item — this is the core rule

- **Single-hop swap or bulk replacement** (swap function A for B, batch import change, replace one helper with a library) → **ONE line**: `<area>：現在 X → 改成 Y`. Do NOT inflate these into multi-step chains; padding a one-liner is the #1 way the contract loses focus.
- **A change that alters several execution-path steps** (a login/locale-decision flow, a value-format change that cascades downstream) → **trace it as a full behavior chain**: write the 現在 chain and the 改成 chain step-by-step and mark the diff. These are the only items that earn the expanded form.

## Format rules

- **Concise first, key points stand out.** The whole contract SHOULD stay under ~25 lines. Most items are one line; only genuinely multi-step flows expand. Writing too much buries the items the user actually needs to check.
- **Concrete names are fine when the name IS the change** — a function-for-function swap, or a value-format migration (`ZH_CN` → `zh-CN`), reads clearest with the actual names/values. Use a concept name instead when a raw symbol would be noise (say "「語言 → 後端數字編號」橋接表" not the constant's identifier). **Never** write `file:line` or import paths — that detail belongs in design/implementation after approval.
- **Format / shape changes MUST get the expanded chain (most error-prone)** — when a change alters the FORMAT or SHAPE of data flowing through the system (enum value renamed, cookie format change, type widened), trace every downstream consumer (cookie / i18n / asset filenames / API body / string-literal comparisons / backend mapping keys / …). Reviewers miss these because they read for "what changes" not "what downstream assumes about the old shape".
- **New-feature user flows need a terminal state** — an expanded user-flow chain MUST end at a user-visible result (success page / email sent / data persisted / error message), not an internal handoff. A flow that stops mid-system leaves a feature half-built.
- **Use action verbs in expanded chains, readable for a non-engineer** — "元件拼 CSS class 名" not "`:class` binding"; "後端產生 token 寫 DB" not "`TokenService.generate()`".
- **Length signal**: if the contract can't fit under ~25 lines even after collapsing one-liners, the change is too large — suggest splitting into sub-changes.

## Why this exists

The single most common cause of review blockers is **a downstream consumer being missed** — a callsite not updated (refactor) or a flow step unaccounted for (new feature). The one-line 現在 → 改成 entries catch "you forgot to replace X" or "you changed it to the wrong thing"; the expanded behavior chains catch "you didn't trace this change to its terminal consumers" — the format-mismatch class of bug that otherwise surfaces only deep into review.

## One correction round only

If the user pushes back, incorporate the corrections and proceed — do NOT loop on this checkpoint. More than one round of correction is a signal the contract was under-specified; treat that as self-feedback, not a reason to keep asking.

When invoked standalone (not from `/propose` or `/quick`): after the user confirms (or corrects once), hand control back to whatever was driving the work — a native coding session, a plan, or the calling skill. This gate produces no files; its only output is a confirmed shared understanding.
