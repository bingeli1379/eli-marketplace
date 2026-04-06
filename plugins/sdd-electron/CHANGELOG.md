# Changelog

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
