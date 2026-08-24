# Changelog

## [1.0.5] - 2026-08-24

### Changed
- Shorter name in the Codex plugin list — "SDD Electron" instead of "SDD — Electron Pack", matching the rest of the SDD family.

## [1.0.4] - 2026-08-04

### Fixed
- The Electron skill's description was a tour of everything it can do, twice the length it needed and competing with unrelated requests. It now states when to use it — you want to drive, automate or test a running Electron app — so it loads on the right ask and stays quiet otherwise.

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.0.3] - 2026-07-12

### Changed
- The Electron engineer now detects and matches your project's existing setup (Electron version, build tool, project layout) before writing code, instead of assuming a fixed stack — its security rules (context isolation, sandbox, IPC allow-listing) stay non-negotiable.

## [1.0.2] - 2026-06-24

### Changed
- The Electron engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.0.1] - 2026-06-22

### Changed
- Made the TresJS 3D skill activate for any Vue + Three.js work, instead of being tied to a specific app.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the Electron desktop/game engineer and its Electron desktop/game skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add Electron desktop/game support to the spec-driven workflow.
