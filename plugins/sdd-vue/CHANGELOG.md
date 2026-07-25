# Changelog

## [1.0.3] - 2026-07-25

### Fixed
- The Tailwind review guidance was written for another project's codebase: it told the assistant to import components from a package that does not exist outside that repo and to respect design tokens in files you do not have. It now inspects your own project first — your Tailwind version, your tokens, your component folder — and reports against those.
- Styling skills are now actually reachable. Nothing previously pointed the frontend or review assistant at them, so they never loaded; they now load when your repo has the matching toolchain (Tailwind or UnoCSS) and the work touches styles.

### Added
- Tailwind reviews now catch v3-era classes left in a v4 project, including the silent case: `shadow-sm` still works in v4 but means one step heavier than it used to, so nothing errors and the design is subtly off.

## [1.0.2] - 2026-06-24

### Changed
- The Vue/Nuxt engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.0.1] - 2026-06-22

### Changed
- Sharpened when each Vue skill activates (API reference vs. best-practice standards vs. component testing), reducing overlap so the most relevant guidance loads.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the Vue/Nuxt frontend engineer and its Vue/Nuxt frontend skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add Vue/Nuxt frontend support to the spec-driven workflow.
