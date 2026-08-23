# Changelog

## [1.2.1] - 2026-08-23

### Changed
- The .NET engineer now treats every concrete tool named by the always-loaded best-practices guide as a suggestion. That guide is mirrored from a general catalogue and had only been overridden on the question of comments, so its choice of test framework read as authoritative — and it disagrees with both this pack's own defaults and the projects it runs against. The test framework, assertion library and mocking library are taken from a test file already in the project, and sections covering stacks a project does not use are set aside the same way.

## [1.2.0] - 2026-08-05

### Changed
- The .NET engineer no longer adds XML documentation comments to ordinary internal service code. Two of the guides it always loads disagreed — one asked for full XML docs on every public member, the other says comments default to none — with nothing saying which wins. XML docs are now for a published API surface, where someone in another repo reads them; for internal code the project's own habit decides, and if its existing public members have none, yours do not get them either.

## [1.1.3] - 2026-08-04

### Fixed
- The gRPC guidance described what it covers instead of when it applies, so it competed with its neighbours for the same request. It now states the situation that should reach it, which is what decides whether the right one loads.

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.1.2] - 2026-07-25

### Changed
- Refreshed the bundled .NET skills from upstream — authentication, minimal APIs, resilience, and gRPC guidance are all current again.

## [1.1.1] - 2026-06-24

### Changed
- The .NET engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.1.0] - 2026-06-22

### Added
- The pack now bundles the error-handling, caching, resilience, and authentication skills (moved here from core), and the .NET engineer loads them automatically when designing an error strategy, adding caching or Polly resilience, or wiring JWT/Identity authorization.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the ASP.NET / .NET backend engineer and its ASP.NET / .NET backend skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add ASP.NET / .NET backend support to the spec-driven workflow.
