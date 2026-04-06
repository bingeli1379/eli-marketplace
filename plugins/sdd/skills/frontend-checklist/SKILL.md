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
2. **Know where each function comes from** — verify each destructured function exists in that composable's source; store values belong in `computed(() => store.state.X)`, not composables
3. **Top-level await is a silent trap** — `await` at top level of `<script setup>` silently requires `<Suspense>`; wrap in IIFE or `onMounted`
4. **Prefer computed over watch** — only use `watch` for genuine side effects (API calls, DOM, logging); if it just derives a value, use `computed`
5. **SFC block order** — `<script setup>` → `<template>` → `<style>`; during reordering, diff carefully to avoid losing template elements
6. **Use each accessor in its correct per-side form — don't "unify"** — where the project's framework exposes a *template global* that is also available as a composable (Vue Router's `$route`/`$router`; a store or i18n global **only if the project registers one** — e.g. Vuex `$store`, or vue-i18n `$t` with `globalInjection`), use the global in templates and the composable (`useRoute()` / `useRouter()` / `useI18n()` / store) in script. Do NOT rewrite one into the other to "unify" style. **Stack-dependent**: Pinia exposes no `$store`, and Composition-mode i18n may not expose `$t` — in those projects use the composable form on both sides. This rule governs only the dual-form router/store/i18n accessors; composable-returned data (`const { items } = useX()`) is of course rendered directly in templates.
7. **Composable usage must be explicit** — destructure specific members; never use rest spread (`const { ...xxx } = useXXX()`)
8. **Template variables must match their scope** — `v-for` loop vars, `$event` params, `v-model` args must exactly match declared names and types
9. **Use `as const` objects instead of `enum`** — `as const` with derived `typeof` union types; no TypeScript `enum`
10. **Prefer named exports over `export default`** — only use default export where framework requires it (Nuxt config/plugins, Vue pages/layouts, Vite config)
11. **Public APIs need both compile-time types and runtime guards** — when authoring a library/plugin, narrow the public TS type to what the function actually consumes (don't widen to absorb caller-side normalization). On invalid input from JS callers or `as`-casted TS code, emit `console.warn` (function name + offending parameter + fallback used) and return a documented fallback — never throw, never silently drop. Internal-only functions skip the guards.

---

## Post-Implementation Checklist — verify after writing code

### Reactivity & Refs

- [ ] All `ref()` wrapped objects accessed with `.value` in script code
- [ ] All computed refs accessed inside functions include `.value`
- [ ] Computed property references match their actual declared variable names
- [ ] Form/class instances that need method calls are wrapped in `ref()` if reactive

### Computed vs Watch

- [ ] Every `watch` justified — not just deriving a value that `computed` could handle
- [ ] `watch` only used for genuine side effects (API calls, DOM manipulation, logging, external system interaction)

### Composable Source Attribution

- [ ] Function destructures attributed to the CORRECT composable — cross-referenced against source file
- [ ] Store-derived values accessed via `computed(() => store.state.X)`, NOT from composables
- [ ] Each destructured function verified to actually exist in the composable it's imported from
- [ ] No rest spread destructuring on composables (`const { ...xxx } = useXXX()` is forbidden)
- [ ] Composable destructuring explicitly lists each used member

### Async Operations

- [ ] No top-level `await` in `<script setup>` scope (wrapped in async IIFE or `onMounted`)
- [ ] All async function calls that need to block are preceded with `await`
- [ ] Execution order preserved — dependent operations inside the same IIFE, not after it

### Composition API Patterns

- [ ] No side effects inside `computed()` — extracted to `watchEffect()` or lifecycle hooks
- [ ] `useTemplateRef()` or `ref` attribute used instead of `getCurrentInstance()` for DOM access
- [ ] Event listeners in `onMounted` have corresponding cleanup in `onUnmounted`
- [ ] No empty `watch()` or `watchEffect()` left behind
- [ ] All emitting components have explicit `defineEmits()` declaration
- [ ] Event names in template match declared emit names

### SFC Structure

- [ ] `<style>` blocks are OUTSIDE `<template>`
- [ ] SFC order: `<script setup>` → `<template>` → `<style>`
- [ ] Template elements not accidentally removed/moved during reordering
- [ ] No duplicate `<script>` blocks
- [ ] `<script setup lang="ts">` has correct `lang` attribute

### Template Globals

- [ ] For a router/store/i18n accessor the project exposes as BOTH a template global and a composable, each side uses its own form (`$route`/`$router` etc. in template; `useRoute()`/`useRouter()`/`useI18n()`/store in script) — not "unified" to one. Applies only to globals the framework actually registers (Pinia has no `$store`; Composition-mode i18n may not expose `$t`)
- [ ] A dual-form accessor's composable (`useRoute()` / `useRouter()` / `useI18n()` / store) is imported in script ONLY when the value is used in script logic — if it is only needed in the template, use the global there and skip the script import
- [ ] Composable-returned data refs ARE rendered directly in templates — this rule does not forbid that; it governs only the dual-form router/store/i18n accessors

### Localization (i18n)

- [ ] New user-facing strings are externalized to i18n keys — not hardcoded literals in template or script
- [ ] New keys exist in the project's **source/base locale** (the one `fallbackLocale` and any translation pipeline read from). Filling the other locales is project-specific — a TMS (Lokalise/Crowdin) + `fallbackLocale` populates them out-of-band, so do **NOT** assume every key must be present in every locale file; follow the project's localization workflow

### Event Handling

- [ ] Event handlers pass required arguments (`$event` where needed)
- [ ] `v-for` loop variable names match their usage in template
- [ ] `v-model` update handlers receive the correct argument type
- [ ] Dynamic `:is` bindings resolve to valid component references

### TypeScript Patterns

- [ ] No `enum` used — all enumerations use `as const` objects with derived `typeof` union types
- [ ] Existing `enum` encountered during modification is **left as-is to match surrounding code** unless the task is explicitly that migration — flag it for a dedicated migration rather than converting as a drive-by (consistency outweighs an isolated improvement)

### Module Exports

- [ ] No `export default` used — all exports are named (`export function`, `export const`, `export type`)
- [ ] Only framework-required files use default export (Nuxt config/plugins, Vue pages/layouts, Vite config)
- [ ] Existing `export default` encountered during modification is **left as-is unless the task targets it** — flag for a dedicated migration rather than converting as a drive-by; never touch framework-required defaults

### Public API Boundaries (library/plugin authoring)

- [ ] Public exports declare narrow TS types matching what the function actually consumes (no `unknown` / `any` to dodge the contract; do not widen to absorb caller-side normalization)
- [ ] Every public entry point validates runtime inputs (`typeof`, `Array.isArray`, `instanceof`, shape check, or a schema validator) before using them
- [ ] Invalid input emits `console.warn` (function name + offending parameter + fallback used) and returns a documented fallback — never throws, never silently drops

### Data Fetching (Nuxt)

- [ ] No raw `$fetch` in components — `useFetch` / `useAsyncData` used for SSR safety
- [ ] Reactive watch sources correct for parameterized fetches
- [ ] Error and loading states handled

### tsconfig.json conventions (Vite projects)

Vite owns transpilation; `tsc` is only a type-checker. An app's tsconfig that emits `.js` files next to its sources creates stale compiled artifacts that shadow the real source files, confuse tooling scans, and reappear every time `tsc -b` runs from a parent solution file.

- [ ] **Vite-bundled apps** (`apps/*` with `vite build` as the production command): `compilerOptions.noEmit: true`. `tsc` runs for type-check only; no `.js` output.
- [ ] **Vite-bundled libraries** (`packages/*` that publish `.d.ts`): `compilerOptions.emitDeclarationOnly: true`. `tsc` emits types, Vite emits the JS bundle.
- [ ] Root `tsconfig.json` solution file references each package's tsconfig via `references: [{ "path": "./packages/..." }]`. Running `tsc -b` from root traverses every reference, so any child tsconfig missing `noEmit` / `emitDeclarationOnly` will emit unwanted files on every build.
