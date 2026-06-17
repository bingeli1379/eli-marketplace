# Changelog

## [1.6.0] - 2026-06-18

### Added
- `/commit` splits a batch of uncommitted changes into separate commits by topic instead of lumping them together, and supports scoped and breaking-change messages (e.g. `feat(scope):`, `feat!:`)
- `/review-prompt` adds a `--report-only` mode that lists issues without editing your files

### Changed
- `/commit` is faster and lighter — it skips generated and lock files and only reads the diffs it needs
- `/release` supports repos with multiple plugins or packages: it targets one package and writes to that package's own changelog

### Fixed
- `/review-prompt` now detects prompt files inside nested plugin folders, so auto-detection works without listing files by hand

## [1.5.0] - 2026-06-04

### Changed
- `/release` now bumps every version manifest a plugin ships (e.g. both Claude and Codex) to the same version in one pass, so they no longer drift out of sync
- `/release` changelog entries now put accuracy first — wording stays concise, but never at the cost of misstating or over-generalizing what actually changed
