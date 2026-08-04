# Changelog

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
