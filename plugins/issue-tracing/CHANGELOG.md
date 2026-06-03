# Changelog

## [1.1.0] - 2026-06-03

### Added
- Reports now identify who or what sent the failing requests, not just which service broke — so you can tell a bot surge from a real user-facing bug.
- The Root Cause now leads with a checklist of what actually changed (a deployment, a dependency, the incoming traffic, or nothing), so an investigation no longer jumps to "external problem" just because no one released.
- Investigations now check code history to tell a deliberate rejection apart from an actual defect before labelling something a bug.

### Fixed
- Error counts no longer stop silently at 10,000, so impact numbers and before/after comparisons in the report are accurate even for large incidents.

### Changed
- The Root Cause section now clearly separates the facts (what triggered the error) from the assessment (what we think went wrong), making reports easier to act on.
