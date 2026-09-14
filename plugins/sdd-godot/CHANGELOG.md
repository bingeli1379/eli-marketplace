# Changelog

## [1.0.5] - 2026-09-14

### Changed
- The agent no longer carries textbook code samples. They pulled it toward copying a typical shape instead of the one your repo already uses, which is the opposite of what it is told to do. It keeps what only it can supply: the signals that identify your stack, which skill to load for which job, and any place it overrides a bundled best-practice skill.
- It also keeps its five detection signals, including the one that stops it promising a web export from a C# project.

## [1.0.4] - 2026-08-24

### Changed
- Shorter name in the Codex plugin list — "SDD Godot" instead of "SDD — Godot Pack", matching the rest of the SDD family.

## [1.0.3] - 2026-08-04

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.0.2] - 2026-07-25

### Changed
- Refreshed the bundled Godot skills from upstream. The physics and UI guidance was substantially rewritten, and new reference material was added on collision layers, physics interpolation, Jolt differences, raycasting, physics troubleshooting, and UI patterns.

## [1.0.1] - 2026-06-24

### Changed
- The Godot engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the Godot game engineer and its Godot game skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add Godot game support to the spec-driven workflow.
