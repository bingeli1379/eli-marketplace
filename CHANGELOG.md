# Changelog

## [1.2.0] - 2026-04-18

### Added (review-prompt)
- `q. Factual accuracy of named references` — verifies step numbers, file paths, function names, and CLI strings actually exist; flags fragile references (e.g., bare step numbers without step names)
- `r. Cross-file consistency` — audits parallel structures across related skills as a group, catching silent divergences when one file is updated and another is forgotten

### Changed (review-prompt)
- Finding format is now mandatory structured (`[file:line] what changed — risk/fix: ...`), replacing the loose `[description]` placeholder
- Language rule moved to top of Step 4 so the report output format and language requirement are seen together
- `k. Checklist rules` now explicitly resolves the j/k conflict: battle-tested content with rationale always wins over "cut verbose explanations"
- Step 1 now explicitly states the skill assumes Claude Code plugin structure (`agents/*.md`, `skills/*/SKILL.md`)

### Removed (review-prompt)
- `For Checklist files` section — `i. Item preservation` folded into `For Skill files` and broadened to cover any bullet list or enumerated section

## [1.1.1] - 2026-04-14

### Changed
- Changelog entries now focus on what matters to you — shorter, clearer, no commit hashes
