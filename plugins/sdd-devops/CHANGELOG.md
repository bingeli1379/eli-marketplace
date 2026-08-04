# Changelog

## [1.0.4] - 2026-08-04

### Fixed
- The GitLab CI guidance described what it covers instead of when it applies, so it competed with its neighbours for the same request. It now states the situation that should reach it, which is what decides whether the right one loads.

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.0.3] - 2026-07-25

### Changed
- Refreshed the bundled Docker and CI/CD skills from upstream, including expanded Docker guidance.

## [1.0.2] - 2026-06-24

### Changed
- The DevOps engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.0.1] - 2026-06-22

### Changed
- The DevOps engineer now loads GitLab CI guidance only when the project actually uses GitLab CI (and GitHub Actions guidance for GitHub projects), instead of always assuming GitLab.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the DevOps engineer and its DevOps skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add DevOps support to the spec-driven workflow.
