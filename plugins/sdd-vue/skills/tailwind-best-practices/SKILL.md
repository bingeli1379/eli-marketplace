---
name: tailwind-best-practices
description: >
  Use when reviewing or refactoring existing Tailwind CSS — design-token consistency,
  repeated utility clusters that should be a component, arbitrary values that bypass the
  scale, and v3-era classes left in a v4 codebase. For writing new Tailwind (utilities,
  config, dark mode, responsive) use the tailwindcss skill.
user-invocable: false
---

# Tailwind Best Practices (review / refactor lens)

Judge Tailwind that already exists. Every finding must point at the project's **own** design system — the tokens in its config or `@theme` block, its own component library — never at an external one.

## Detect the project's system first

There are no universal token names or component paths. Before reporting anything, establish:

1. **Version** — v4 if the CSS has `@import "tailwindcss"` and an `@theme` block; v3 if there is a `tailwind.config.{js,ts}` with `content`/`theme.extend` and `@tailwind base/components/utilities`. Both can coexist mid-migration; say which files are on which.
2. **The token vocabulary** — read the `@theme` block (v4) or `theme.extend` (v3). These names ARE the allowed scale. A value outside it is a finding; a value inside it is not, however unusual it looks.
3. **The component layer** — where shared UI lives in *this* repo (`components/ui/`, a workspace package, nothing at all). If the repo has no component layer, "extract a component" is a suggestion, not a violation.

Skip any check below that the project's own setup makes inapplicable. A rule you cannot anchor to something in the repo is not a finding.

## What to flag, in priority order

### 1. Token bypass (highest value)

- An arbitrary value (`w-[327px]`, `text-[#3b82f6]`, `p-[13px]`) where a scale token exists. Name the token it should be.
- A raw hex / rgb color anywhere in a utility, when the theme defines a semantic color.
- Off-scale spacing that visibly breaks rhythm (`mt-[7px]` next to `mt-2` siblings).
- **Legitimate exceptions**: a one-off dimension dictated by an asset or third-party embed, and values that genuinely have no token (often `h-`/`w-`). Flag those as accept-with-comment, not as violations.

### 2. Repetition that should be a component or a token

- The same utility cluster (roughly 5+ classes) repeated 3+ times → extract a component in the project's own component layer, or a token if it is purely a value.
- Do NOT recommend `@apply` as the default fix: it moves the duplication into CSS and loses the utility-scan benefits. Reach for it only for a genuinely global primitive the project already styles that way.

### 3. Class-list health

- Conditional classes assembled by string concatenation → use the project's existing helper (`clsx`, `cva`, `tailwind-merge`, `twMerge`); do not introduce a new dependency for this if none exists.
- Conflicting utilities in one list (`p-2 p-4`, `flex grid`) — the later one silently wins; this is almost always a merge artifact.
- Dead responsive/state variants: a `hover:` on a non-interactive element, an `sm:` that the layout can never reach.

### 4. v3-era classes in a v4 codebase

v4 renamed and removed utilities, and models trained on v3 keep emitting the old ones. When the project is on v4, these are stale-syntax findings:

| v3 (stale) | v4 | Note |
|---|---|---|
| `bg-opacity-50`, `text-opacity-75`, `border-opacity-*` | `bg-black/50`, `text-gray-900/75` | The `*-opacity-*` utilities were removed; use the slash modifier |
| `shadow-sm` (meaning the smallest) | `shadow-xs` | The whole shadow scale shifted down: old `shadow` → `shadow-sm` |
| `blur-sm` (smallest), `rounded-sm` (smallest) | `blur-xs`, `rounded-xs` | Same downward shift as shadows |
| `bg-gradient-to-r` | `bg-linear-to-r` | v4 also adds `bg-radial-*` / `bg-conic-*` |
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` | The directives were removed entirely in v4 |
| JS config for theme values | `@theme { --color-brand: … }` in CSS | v4 is CSS-first; a JS config still works but the two drifting apart is its own finding |

**The shadow/blur/rounded shift is the dangerous one** — `shadow-sm` still *exists* in v4, so nothing errors; the element just renders one step heavier than intended. Compare against the design intent, not against whether the class resolves.

On a project still on v3, none of the above applies — do not "fix" v3 code into v4 syntax outside a deliberate migration.

## Reporting

Group findings by the four categories above, each as `file:line: <what> → <the project's own token/component to use instead>`. State the project's version and token source once at the top so the reader can check your anchor. Token bypass and stale v4 syntax are the findings worth blocking on; repetition and class-list health are suggestions unless the project's own conventions make them rules.
