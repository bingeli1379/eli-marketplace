# Changelog

## [1.1.4] - 2026-08-24

### Changed
- Shorter name in the Codex plugin list — "SDD Python" instead of "SDD — Python Pack", matching the rest of the SDD family.

## [1.1.3] - 2026-08-04

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.1.2] - 2026-07-25

### Changed
- Refreshed the bundled prompt-engineering and LLM-evaluation skills from upstream.

## [1.1.1] - 2026-06-24

### Changed
- The Python engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.1.0] - 2026-06-22

### Added
- New skills matched to real Python work — async/concurrency patterns, pytest testing patterns, common-mistake review, LLM prompt engineering, and LLM evaluation — loaded automatically when a task calls for them.

### Removed
- Dropped the Microsoft Dataverse skills, which did not apply to the FastAPI, data-pipeline, ML, and LLM work this pack targets.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the Python backend/ML engineer and its Python backend/ML skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add Python backend/ML support to the spec-driven workflow.
