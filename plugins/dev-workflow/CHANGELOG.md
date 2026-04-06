# Changelog

## [1.9.0] - 2026-07-12

### Added
- New `/review-workflow` command — a deeper, occasional audit companion to `/review-prompt`. It traces a workflow skill's steps to find where the procedure itself breaks (resuming re-does or skips already-done work, a step destroys data a later step needs, contradictory or unhandled steps, crash/edge cases) and sweeps the repo for duplicated content and settings that have drifted out of sync. Report-only by default.
- New `/improve-skill` command — usage-driven and cross-repo. When a marketplace skill misbehaves, misses a case, or feels clunky while you use it in *another* project, it reads what went wrong in that session and patches the skill's source in your local marketplace repo (the git working copy), then validates via the audit commands. It proposes the changes for review first and leaves committing, pushing, and reinstalling to you.

### Changed
- `/review-prompt` now flags a changed instruction that contradicts another instruction in the same file, and — when run right after a commit — reviews the files from your latest commits instead of reporting "nothing to review".
- `/release` is more reliable in multi-package repos: it scopes "what changed" to the package being released (so unrelated merges don't leak into the changelog), finds the correct previous-release baseline even when a recent commit message contains the word "release", can sweep and release every changed sub-package in turn, and re-checks that version files still parse after the bump.

## [1.8.0] - 2026-06-19

### Changed
- `/review-prompt` now reviews your skills with Claude Code as the main target instead of chasing cross-tool compatibility — it no longer flags Claude-specific features as problems to strip out, and assumes support for other tools is added later by a separate build step
- `/review-prompt` adds two new correctness checks: it catches file-read instructions that point to the wrong folder (so bundled files load reliably), and flags speed/model settings placed where they have no effect

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
