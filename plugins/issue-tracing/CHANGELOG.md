# Changelog

## [1.3.0] - 2026-06-25

### Added
- When investigating an internal system, the investigation now loads your environment's logging/monitoring conventions first — real host and index names, field quirks, and any services whose logs live somewhere other than the default place — so it queries the right source instead of guessing. It also turns unreadable log values (encoded message payloads, status codes, ids) into human-readable form when a tool for that is available.

### Fixed
- Investigations no longer freeze partway through. Checking logs or infrastructure metrics used to fire many queries at once and exhaust the backend's connection limit, leaving the run stuck; queries are now paced (and back off to one-at-a-time on errors) so they complete.

## [1.2.0] - 2026-06-03

### Fixed
- Investigations no longer give a false "not found" / "wrong cluster" answer when the logs are there but the query was shaped wrong. Three traps that each silently returned zero results are now closed: (1) a Kibana data view is resolved to its real underlying index by reading the saved object directly, instead of guessing from its display name; (2) that index name is now queried exactly as-is, because tacking on a wildcard quietly skips logs stored in data streams; (3) filters now match how the values are actually stored, instead of assuming a keyword field that may not exist and matching nothing.

### Added
- A "0 hits" diagnostic checklist: before concluding an error doesn't exist, the investigation re-checks the resolved index name, confirms it didn't accidentally add a wildcard, peels back one filter at a time (catching a missing keyword field, or a level saved as "Error" vs "error"), confirms the time window has any data at all, and only then raises a cross-cluster or access question — offering to read the page from the browser when the user can already see it.

### Changed
- The investigation now honors the filters you put in the URL instead of fanning out on its own. If you send a link already filtered to errors, it surfaces those errors and stops; it only pulls extra data (baselines, related services, infrastructure metrics) when you ask for a full root-cause report or when the logs themselves don't explain the failure. Less waiting, fewer needless queries.

## [1.1.0] - 2026-06-03

### Added
- Reports now identify who or what sent the failing requests, not just which service broke — so you can tell a bot surge from a real user-facing bug.
- The Root Cause now leads with a checklist of what actually changed (a deployment, a dependency, the incoming traffic, or nothing), so an investigation no longer jumps to "external problem" just because no one released.
- Investigations now check code history to tell a deliberate rejection apart from an actual defect before labelling something a bug.

### Fixed
- Error counts no longer stop silently at 10,000, so impact numbers and before/after comparisons in the report are accurate even for large incidents.

### Changed
- The Root Cause section now clearly separates the facts (what triggered the error) from the assessment (what we think went wrong), making reports easier to act on.
