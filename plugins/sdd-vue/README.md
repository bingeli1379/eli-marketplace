# sdd-vue

**SDD language pack — Vue / Nuxt frontend.** Extends the [`sdd`](../sdd) core plugin with the
`vue-engineer` agent and Vue / Nuxt frontend skills. Part of the spec-driven multi-agent workflow.

## What it adds

- **Agent** `sdd-vue:vue-engineer` — Vue ecosystem (Nuxt SSR, Vue 3 Vite SPA, legacy Vue 2, single-spa): components, pages, composables, Pinia stores, styling, build tooling, and frontend testing.
- **Skills** (23): accessibility, antfu, core-web-vitals, create-adaptable-composable, frontend-testing-best-practices, nuxt, pinia, pnpm, tailwind-best-practices, tailwindcss, typescript-advanced-types, unocss, vite, vitest, vue, vue-best-practices, vue-debug-guides, vue-jsx-best-practices, vue-pinia-best-practices, vue-router-best-practices, vue-testing-best-practices, vueuse-functions, web-design-guidelines.

## Install

```
/plugin install sdd-vue@titansoft-marketplace
```

Declares `dependencies: ["sdd"]`, so installing this pack pulls in the `sdd` core
plugin automatically. The agent eager-loads core skills (agent-guidelines,
engineering-checklist, test-driven-development, …) cross-plugin by bare name.

## How it fits

The core orchestrator dispatches this pack's agent by its namespaced `subagent_type`
(`sdd-vue:vue-engineer`) per the routing table in `sdd/references/agent-routing.md`. If this
pack is not installed, core falls back to a general-purpose agent and suggests
installing it. See the [`sdd` README](../sdd/README.md) for the full workflow and the
maintenance guide for adding/maintaining packs.
