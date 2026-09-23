---
name: frontend-checklist
description: >
  Mandatory principles and checklist for frontend engineers when writing or modifying JS/TS/Vue code.
  MUST be loaded when: implementing frontend tasks, writing Vue components, composables,
  migrating Options API to Composition API, refactoring SFC structure, authoring a JS/TS
  library/plugin, or reviewing frontend code.
  Covers Vue reactivity, Composition API patterns, SFC structure, async pitfalls, and
  public API boundary design (compile-time types + runtime guards) for library authors.
user-invocable: false
---

# Frontend Checklist

**Derived from real-world Vue/Nuxt production bugs. Applies when writing or modifying JS/TS/Vue code.**

Also load `engineering-checklist` — it contains common rules for all engineers.

## Principles — follow these while writing code

1. **`.value` is not optional** — `ref()` objects MUST use `.value` in script; templates auto-unwrap but script does not
2. **Know where each function comes from** — verify each destructured function exists in that composable's source; store values belong in a `computed` over the store (`store.state.X` in Vuex, `store.x` in Pinia), not in composables
3. **Top-level await is a silent trap** — `await` at top level of `<script setup>` silently requires `<Suspense>`; wrap in IIFE or `onMounted`, and keep dependent operations inside the same IIFE so their order survives
4. **Prefer computed over watch** — only use `watch` for genuine side effects (API calls, DOM, logging); if it just derives a value, use `computed`
5. **SFC block order** — `<script setup>` → `<template>` → `<style>`; during reordering, diff carefully to avoid losing template elements
6. **Use each accessor in its correct per-side form — don't "unify"** — where the project's framework exposes a *template global* that is also available as a composable (Vue Router's `$route`/`$router`; a store or i18n global **only if the project registers one** — e.g. Vuex `$store`, or vue-i18n `$t` with `globalInjection`), use the global in templates and the composable (`useRoute()` / `useRouter()` / `useI18n()` / store) in script, and import the composable only when script logic actually uses the value. Do NOT rewrite one into the other to "unify" style. **Stack-dependent**: Pinia exposes no `$store`, and Composition-mode i18n may not expose `$t` — in those projects use the composable form on both sides. This rule governs only the dual-form router/store/i18n accessors; composable-returned data (`const { items } = useX()`) is of course rendered directly in templates.
7. **Composable usage must be explicit** — destructure specific members; never use rest spread (`const { ...xxx } = useXXX()`)
8. **Template variables must match their scope** — `v-for` loop vars, `$event` params, `v-model` args must exactly match declared names and types
9. **Use `as const` objects instead of `enum`** — `as const` with derived `typeof` union types; no TypeScript `enum`. An existing `enum` met during a modification is **left as-is to match surrounding code** unless the task is that migration — flag it rather than converting as a drive-by
10. **Prefer named exports over `export default`** — only use default export where framework requires it (Nuxt config/plugins, Vue pages/layouts, Vite config). An existing `export default` met during a modification is left as-is unless the task targets it; never touch framework-required defaults
11. **Public APIs need both compile-time types and runtime guards** — when authoring a library/plugin, narrow the public TS type to what the function actually consumes (don't widen to absorb caller-side normalization). On invalid input from JS callers or `as`-casted TS code, emit `console.warn` (function name + offending parameter + fallback used) and return a documented fallback — never throw, never silently drop. Internal-only functions skip the guards.
12. **New user-facing strings go through i18n keys**, added to the project's **source/base locale** (the one `fallbackLocale` and any translation pipeline read from). Filling the other locales is project-specific — a TMS (Lokalise/Crowdin) + `fallbackLocale` populates them out-of-band, so do **NOT** assume every key must be present in every locale file; follow the project's localization workflow
13. **Nuxt data fetching goes through `useFetch` / `useAsyncData`**, not raw `$fetch` in components — SSR safety, and the watch sources of a parameterized fetch must be the reactive inputs it depends on
14. **A multi-line template comment whose repo precedent is split indents one step in** — a `<!-- -->` spanning lines puts its continuation one indent step past the `<!--` line, and a lone `-->` back level with it; that is what `vue/html-comment-indent` enforces (2 spaces per step unless configured). No preset enables that rule, so two siblings in one repo routinely disagree, and copying the nearest one is then not a convention. **Where the repo's multi-line comments agree, that is the convention and `engineering-checklist` principle 1 outranks this one** — in writing and in review alike. Where the repo could enforce it, say so in your report rather than editing its lint config as a drive-by

## tsconfig.json conventions (Vite projects)

Vite owns transpilation; `tsc` is only a type-checker. An app's tsconfig that emits `.js` files next to its sources creates stale compiled artifacts that shadow the real source files, confuse tooling scans, and reappear every time `tsc -b` runs from a parent solution file.

- **Vite-bundled apps** (`apps/*` with `vite build` as the production command): `compilerOptions.noEmit: true`. `tsc` runs for type-check only; no `.js` output.
- **Vite-bundled libraries** (`packages/*` that publish `.d.ts`): `compilerOptions.emitDeclarationOnly: true`. `tsc` emits types, Vite emits the JS bundle.
- Root `tsconfig.json` solution file references each package's tsconfig via `references: [{ "path": "./packages/..." }]`. Running `tsc -b` from root traverses every reference, so any child tsconfig missing `noEmit` / `emitDeclarationOnly` will emit unwanted files on every build.
