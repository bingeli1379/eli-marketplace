# Changelog

## [1.7.1] - 2026-06-19

### Fixed
- `/review-prompt` no longer crashes on startup — an example in its own instructions was being run as a command and is now plain text

## [1.7.0] - 2026-06-18

### Added
- `/review-prompt` now checks that your skills work across AI tools — it flags syntax that only runs in one tool (e.g. Claude Code) and breaks in others like Codex, keeps settings that are harmlessly ignored elsewhere, and auto-fixes what it safely can

### Fixed
- `/commit` now works correctly in AI tools other than Claude Code — it no longer depends on Claude-only command syntax that left it acting on empty context elsewhere

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
