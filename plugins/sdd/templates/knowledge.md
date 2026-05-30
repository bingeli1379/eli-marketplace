# Project Knowledge

<!--
  Format: one line per entry. `<project-specific fact>. <path:line pointer>.`
  Past pain only — never speculative ("if future code does X, do Y").
  If you need a paragraph, you are explaining logic — point to the file instead.

  ❌ BAD examples (do not write entries like these):
    - "Be careful with locale handling."           — too vague, no path, no concrete trigger
    - "If we ever migrate to X, do Y."             — speculative; future-tense entries belong nowhere
    - "Plugin order matters because Vue/Nuxt..."   — generic framework knowledge, not project-specific
    - "Order: validate → calculate tax → save..."  — logic walkthrough; point to the file instead
-->

## Domain

<!-- Business rules a new dev cannot derive from the code alone.
     e.g. Order cancellation blocked once status=Paid. `Orders/Order.cs:42`. -->

## Dev Environment

<!-- Local setup, mocks, test data, env flags, mock-vs-real gaps.
     e.g. MSW handlers paginate; real API does not. `mocks/handlers.ts:14`. -->

## Gotchas

<!-- Cross-file coupling, plugin/middleware ordering, cache key partitioning, fallback modes.
     e.g. `advancedFormat` plugin needs `enforce: 'pre'` or `Q` token rendering breaks. `nuxt.config.ts:14`. -->

## External Dependencies

<!-- Upstream service quirks: timeout caps, pagination limits, auth oddities, response shape.
     e.g. Upstream caps page size at 50 despite docs saying 100. `services/foo.ts:88`. -->

<!--
  Knowledge entries rot when the code they point to changes.
  Run `/knowledge-audit` periodically to verify each entry against the current codebase
  and prune anything stale.
-->
