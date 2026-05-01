# Knowledge Seed Candidates

Detailed sources + filter passes for Phase 1 step 4 of `/esdd-init`. Load this file when SCAN starts collecting knowledge.md seed candidates.

---

## Goal

Harvest the project's existing operational tribal knowledge that is **already documented in code or env config** — env hints and informational code comments — so a fresh project does not start with an empty `knowledge.md`. Surviving candidates are surfaced inline in the SCAN report for **interactive batch confirmation** before any write to `knowledge.md`. AI never writes a candidate without explicit user approval — behavioral claims are easy to get wrong from naming alone.

---

## Sources to scan (three — all gated for high signal-to-noise)

| Source | What to extract | Target category |
|---|---|---|
| `.env.example` / `.env.sample` / `.env.template` | env vars whose names are non-obvious OR have inline comments explaining purpose / toggling behavior | Dev Environment |
| Code comments matching informational patterns | `// triggered when …`, `// see also …`, `// note:`, `// because …`, `// only X when Y`. Skip `HACK` / `FIXME` / `XXX` — those are unresolved TODO markers, not stable knowledge. | Gotchas |
| **Named-symbol historical rules** from CLAUDE.md / AGENTS.md / `.cursor/rules/` (gated — see below) | "do not use \`OldName\`" / "prefer \`NewName\` over \`OldName\`" / "the deprecated \`X\` should not be imported". Only when the rule names a single concrete code symbol in backticks. | Gotchas |

**Explicitly dropped sources** (too noisy to harvest reliably):
- README / CONTRIBUTING / docs/**.md (often outdated; circular references)
- package.json scripts (rarely yield stable operational facts)
- Vague historical rules without a named symbol (e.g. "the old auth flow")
- Third-party deps with internal-helper overlap (weak signal)

These get picked up organically through `/esdd-complete` after each change instead.

### Named-symbol historical rule — gating rules

A historical rule from `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/` qualifies as a candidate **only when ALL conditions hold**:

1. The rule sentence contains **at least one identifier in backticks** that looks like a code symbol (camelCase / PascalCase / snake_case / kebab-case prefixed with `use*` / `*Service` / `*Adapter` / etc.). Vague phrases like "the legacy stuff" → drop.
2. The symbol can be located in code via `rg '\b<symbol>\b'` (no `-t` filter — let ripgrep search every tracked file so language-specific filters do not silently drop symbols in Go / Rust / Java / Vue / etc.). **Symbol resolves to ≥1 hit** → candidate kept; **0 hits** → silently dropped (the rule has aged out).
3. Pick the symbol's **definition site** as citation (`function <symbol>` / `class <symbol>` / `const <symbol>` / `export ... <symbol>`). If only call-sites exist (rare; happens when symbol comes from a dep), pick the first call-site. If neither resolves clearly → drop.
4. The candidate text must follow the form `Avoid <symbol> — <reason in ≤12 words>.` — paraphrase the rule into one line. Drop if the paraphrase requires more than one clause.

**Citation rule overrides the markdown-citation ban**: even though the rule originated from `CLAUDE.md`, the candidate's `path:line` MUST point at the resolved code symbol (per gate 3), never at the markdown source. If gate 3 fails, the candidate is dropped — the markdown citation is never accepted as a fallback.

**Conservative count**: at most 3 historical-rule candidates per init even before the global cap-of-5 applies. Surface a `Skipped N historical rules from CLAUDE.md/AGENTS.md (no resolvable symbol)` line in the BUILD summary so the user knows the rest exist and can hand-add them.

---

## Hard cap

Surface **at most 5 candidates** in the SCAN report. If more survive the filters, rank by signal strength (env vars with inline comments > code comments > everything else) and drop the rest. False knowledge is worse than missing knowledge — `/esdd-complete` will pick up real operational facts as the project moves forward.

---

## Hard requirement — Cite-or-Skip

Every candidate MUST attach `path/file.ext:start-end` line range and a 3–5 line snippet of the cited content. Candidates that cannot be pinned to a specific line range are dropped silently — naming alone is not enough.

**Citations must point to code files, not markdown docs**: valid targets are `.ts` / `.tsx` / `.js` / `.vue` / `.cs` / `.csproj` / `.py` / `.go` / `.rs` / `.sql` / config files (`*.config.ts`, `nuxt.config.ts`, `package.json`, `appsettings.json`, etc.) — anything that represents the **actual behavior**. Citations pointing to other markdown documents (`CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/**.md`) are **silently dropped** — they create circular references because `knowledge.md` is meant to capture facts not already living in those docs.

---

## Self-skeptic pass

Run on every candidate before keeping it:

1. Re-read ONLY the cited snippet (do not re-explore).
2. Ask: does the candidate text match what the snippet actually does, not what its identifier suggests?
3. If they mismatch → either rewrite the entry to describe the actual behavior, or drop it. Mark surviving rewrites with `⚠️ Name-vs-impl mismatch:` so the user sees the warning during review.

---

## Counter-example pass

Cheap grep-based check:

1. Extract the entry's central claim (e.g., "X only triggers when country=MM").
2. Grep the codebase for tokens that could contradict the claim (`country !==`, `country === '`, etc.).
3. If a contradicting branch is found → either narrow the claim to the verified case, or drop it.

---

## Conservative default

When in doubt, drop. False knowledge is worse than missing knowledge.

---

## Dedup against audited entries

Run this **after** the existing-entry audit (Phase 1 step 4.5) finishes, before rendering the SCAN report:

Take the `✅ Still valid` and `⚠️ Needs rewrite` entries from the audit and use them to filter the raw candidate list collected here. Drop any new candidate whose claim semantically overlaps an audited entry (same `path:line` neighborhood + same direction of claim). False duplicates pollute the SCAN report and make the user decide twice on the same fact.

**Phase 1 execution order is therefore**: detection (1–3) → seed scan (4, collect raw candidates, defer dedup) → audit (4.5) → dedup pass (filter step 4 output using step 4.5 results) → cap at 5 → SCAN report. The candidate list is **not** finalized until after dedup + cap runs.
