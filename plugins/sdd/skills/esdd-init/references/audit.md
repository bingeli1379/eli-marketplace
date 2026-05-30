# Existing knowledge.md Audit

Detailed audit pipeline for Phase 1 step 4.5 + Phase 2 step 3a-bis (apply audit decisions). Load this file **only when** `feature-spec/knowledge.md` exists with real entries (more than skeleton + HTML comments) AND the user did NOT pick "Regenerate (overwrite)" for it in Phase 0.

Goal: re-verify each existing entry against the current codebase so the user can keep, rewrite, or drop drifted entries during the same SCAN pass — no separate `/knowledge-audit` round trip needed for the init flow.

---

## When to skip

Skip this entire phase when **any** of the following is true:
- `feature-spec/knowledge.md` does not exist.
- The file contains only the canonical skeleton (headings + HTML guidance comments + zero real entries).
- The user picked "Regenerate (overwrite)" for `knowledge.md` in Phase 0 (file will be wiped anyway).

---

## Per-entry pipeline

For each existing entry under any category heading:

1. **Parse citation** — extract `path/to/file:start-end`. If no citation present → mark `❓ Uncited`, skip remaining steps for this entry.
2. **Resolve file + lines** — check the file path exists and the line range is in bounds. If file missing OR line range out of bounds → mark `❌ Stale (citation broken)`.
3. **Re-read snippet** — read ONLY the cited line range. Do not re-explore.
4. **Self-skeptic check** — does the entry's central claim still match what the snippet actually does (not what an identifier suggests)? If snippet drifted (refactored, behavior moved, condition flipped, file shifted but lines now point at different code) → mark `⚠️ Needs rewrite` and draft a corrected one-line claim that describes the current behavior.
5. **Counter-example grep** — extract the entry's central claim, grep for tokens that could contradict it (`X !==`, `X === '`, alternative branches, feature flags). If a contradicting branch is found and the entry does not already narrow to it → mark `⚠️ Needs rewrite` and draft a narrower claim.
6. **Otherwise** → mark `✅ Still valid`.

---

## Conservative default

When uncertain between "still valid" and "needs rewrite", pick `⚠️ Needs rewrite` so the user sees it. When uncertain between "needs rewrite" and "stale", pick `⚠️ Needs rewrite` — never `❌ Stale` unless the citation truly does not resolve. AI never auto-deletes; the user always makes the final call via the audit-decision batch question.

---

## Output

A classified list of every existing entry, with original line, classification, citation status, and (for `⚠️`) the suggested rewrite. This list feeds the SCAN report's "既有 knowledge.md 審計" section. Indices use **A-prefix** (`A1`, `A2`, ...) to disambiguate from new candidates which use C-prefix.

Format inside the SCAN report (Traditional Chinese conversation, English file content):

```
A1. [⚠️ 建議改寫] <既有條目原文>
    Citation: `path:line` (resolves)
    Issue: <one-line drift description in Chinese>
    Suggested: <new one-line claim — file content stays in English>
A2. [❌ Citation 失效] <既有條目原文>
    Citation: `path:line` (file missing / lines out of bounds)
A3. [❓ 無 citation] <既有條目原文>
    無 path:line — 請手動審視
```

`✅ 仍有效` 的條目不逐條列出（純綠燈，不需用戶決策），只計入 summary。

Summary line: `總條目數 N | ✅ 仍有效 X | ⚠️ 建議改寫 Y | ❌ Citation 失效 Z | ❓ 無 citation W`

---

## Audit-decision question

Asked at SCAN report time, **only** when audit produced ≥1 ⚠️/❌/❓ finding. Use `AskUserQuestion`. Three layouts depending on finding count (AskUserQuestion enforces `options.minItems = 2`, `maxItems = 4`):

### When findings = 1 → single-select Apply / Skip

```
AskUserQuestion({
  questions: [{
    question: "既有 knowledge.md 審計 — 1 條建議要套用嗎？",
    header: "Audit",
    multiSelect: false,
    options: [
      { label: "保留原樣 (推薦)", description: "不動條目，僅在檔案頂部加 audit 摘要註解" },
      { label: "套用 A1",         description: "<A1 action shortened: 改寫 / 刪除 / 加 manual-review 註解>" }
    ]
  }]
})
```

`套用 A1` → apply the entry's action. Anything else (保留原樣 / dismissed / Other) → entry stays unchanged. Always inject the audit-summary HTML comment at top.

### When 2 ≤ findings ≤ 4 → multiSelect (one option per finding)

```
AskUserQuestion({
  questions: [{
    question: "既有 knowledge.md 審計 — 哪些建議要套用？(未勾 = 保留原樣)",
    header: "Audit",
    multiSelect: true,
    options: [
      // up to 4 options, one per finding, ordered by severity (⚠️ first, then ❌, then ❓)
      { label: "A1 ⚠️ <claim shortened>", description: "→ 改寫成: <suggested rewrite shortened>" },
      { label: "A2 ❌ <claim shortened>", description: "→ 刪除（檔案/行號失效）" },
      { label: "A3 ❓ <claim shortened>", description: "→ 加 manual-review 註解" },
    ]
  }]
})
```

User checks the entries to apply. Unchecked / dismissed → the entry stays unchanged. After processing, inject the single dated audit-summary HTML comment at the top of `knowledge.md` noting how many entries went unapplied.

### When findings > 4 → mode-based (cannot fit one-per-finding)

```
AskUserQuestion({
  questions: [{
    question: "既有 knowledge.md 審計：⚠️ <Y> 改寫 · ❌ <Z> 失效 · ❓ <W> 無 citation。怎麼處理？",
    header: "Audit",
    multiSelect: false,
    options: [
      { label: "全部保留 (推薦)",     description: "不動條目，僅在檔案頂部加單一 audit 摘要註解供後續手動處理；最保守，避免誤刪用戶手寫內容" },
      { label: "套用全部建議",        description: "⚠️ → 改寫 · ❌ → 刪除 · ❓ → 加 manual-review 註解" },
      { label: "只套用改寫",          description: "⚠️ → 改寫；❌❓ 保留不動（仍加 summary 註解）" },
      { label: "讓我手動挑",          description: "在 Other 回填 A-prefix 索引（例：A1,A3 或 A1-A3）" }
    ]
  }]
})
```

### Reply mapping

| Layout | User input | Behavior |
|---|---|---|
| single-select (=1) | 套用 A1 | Apply the entry's action. |
| single-select (=1) | 保留原樣 / dismissed / Other | Entry stays unchanged. |
| multiSelect (2–4) | Checked entries | Apply the per-severity action (⚠️→rewrite / ❌→delete / ❓→flag, defined under "套用全部建議" in the Apply audit decisions section below) for each checked entry. Unchecked stay unchanged. |
| multiSelect (2–4) | Empty selection / dismissed | All entries stay unchanged (= "全部保留"). |
| mode-based (>4) | 套用全部建議 | All ⚠️/❌/❓ entries get the per-severity action defined below. |
| mode-based (>4) | 全部保留 / dismissed | All entries stay unchanged. |
| mode-based (>4) | 只套用改寫 | Only ⚠️ entries get rewritten; ❌❓ stay unchanged. |
| mode-based (>4) | 讓我手動挑 (with `<indices>` from Other reply) | Parse `A1,A3` / `A1-A3` etc.; apply the per-severity action (⚠️→rewrite / ❌→delete / ❓→flag, same as 套用全部建議) only to listed entries. Empty / unparseable Other → fall back to "全部保留". |

In **every** case, inject the single dated audit-summary HTML comment at top of `knowledge.md` noting the unapplied count. The conservative default ("never silently delete user-written content") holds for both layouts.

This question is **not** counted against the 3-question gap-filling cap. Skip the question entirely when zero ⚠️/❌/❓ findings.

---

## Apply audit decisions (Phase 2 step 3a-bis)

Runs whenever audit ran in Phase 1 — even when the user dismissed the audit-decision question, the default ("全部保留") still runs to leave entries unchanged and inject the audit-summary HTML comment at the top of the file. There is no "skip entirely" option; if you have findings, you record them.

**Reply normalization**: dismissed / empty selection → treat as "全部保留" (per the audit-decision question's stated default).

Translate the user's mode pick into per-entry actions:

| User picked | Action per ⚠️ / ❌ / ❓ entry |
|---|---|
| 套用全部建議 | ⚠️ → replace original line with the AI-suggested rewrite. ❌ → delete the line entirely. ❓ → leave the entry unchanged and insert an HTML comment `<!-- audit YYYY-MM-DD: no citation, please review -->` on the line directly above the entry. |
| 全部保留 (also: dismissed) | Leave every entry unchanged. Inject a single dated `<!-- audit YYYY-MM-DD: N entries flagged (Y rewrite / Z stale / W uncited), see /esdd-init SCAN report -->` comment at the top of `knowledge.md` so the user can find them later. |
| 只套用改寫 | ⚠️ entries get rewritten in place. ❌❓ stay unchanged. Inject the audit-summary comment at top noting the unapplied ❌+❓ count. |
| 讓我手動挑 (with `<indices>` from Other reply, e.g. `A1,A3`) | Apply the "套用全部建議" actions only to the listed entries; the rest stay unchanged. Inject the audit-summary comment at top noting the unapplied count. If the Other reply is empty or unparseable, fall back to "全部保留". |

### Editing rules

- Operate **in place**: read `knowledge.md`, modify the targeted lines, write back. Never reorder unaffected entries.
- Preserve all category headings and the per-section HTML guidance comments verbatim.
- For ⚠️ rewrites, the new line must follow the same one-line format (`<claim>. <path:line>.`) — if the suggested rewrite spans multiple lines, collapse before writing or downgrade to ❓ behavior.
- For ❌ deletions, do not leave a blank line gap — close up the surrounding entries.
- All injected audit HTML comments are in **English** (per file-content language rule). The comment date must be the actual init run date in ISO format.
- **Audit summary comment is single-instance**: before injecting the audit summary comment at the top of the file, scan for any existing `<!-- audit YYYY-MM-DD: ... -->` summary comment at the file head and **replace** it (do not stack). Only the latest run's summary should remain. The per-entry `<!-- audit ... no citation -->` comments inserted when ❓ entries get applied (via single-select / multiSelect / 套用全部建議 / 讓我手動挑) are positional and accumulate normally — only the head-of-file summary is single-instance.
