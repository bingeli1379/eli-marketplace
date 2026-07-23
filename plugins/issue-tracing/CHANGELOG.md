# Changelog

## [1.6.2] - 2026-07-23

### Changed
- Investigations now run leaner and faster: the tool follows the error's own stack trace from one service to the next and saves the heavy checks (baseline comparisons, infrastructure metrics, cross-service scans) for a single pass that confirms the suspected root cause — instead of re-querying logs and metrics at every step — so you get the answer sooner without losing rigor.
- It also stops over-analyzing once the main error is clear (no longer tallies every minor error type) and reads exactly the log source your link points at before falling back to a broader list — cutting redundant queries.

## [1.6.1] - 2026-07-23

### Changed
- The investigation now stays on where each service is actually deployed: it keeps to the cluster your log link points at, checks each downstream service in its own cluster, and only runs a broad cross-service scan when a shared resource is genuinely implicated — so it stops wasting time querying clusters a service isn't on or chasing unrelated errors.

## [1.6.0] - 2026-07-23

### Added
- When a timeout points at shared infrastructure (a shared cache, database, or the network to it), the investigation now runs one quick cross-service check to tell a single-service problem apart from a fleet-wide infrastructure event — so it stops over-drilling one call chain and pinning the blame on the wrong downstream service.
- When the cause is a shared datastore, it now works out whether the datastore itself or the connection to it is at fault, and tells you which team to confirm with (the network/IT team vs the database team) instead of leaving that open.

### Changed
- The user-facing impact is now read from the actual frontend code — with extra ways to locate it when the obvious search misses — so "what the user saw" is based on evidence instead of a guess.

## [1.5.1] - 2026-07-22

### Fixed
- The investigation now reliably identifies the most common error even on log streams where the message text can't be searched directly — previously it could wrongly conclude a dominant error "didn't exist".
- When a service sends its logs through a newer (OTEL) pipeline, the investigation now finds them by service name instead of wrongly reporting the service had no logs and jumping to a cross-cluster guess.
- Checking the infrastructure of a service with many instances is faster and no longer stalls on oversized metric queries.

## [1.5.0] - 2026-07-22

### Changed
- Give it a log or Grafana link and it now runs the whole investigation on its own — from the filtered logs, down the call chain, to the root cause — and writes the report, instead of stopping after the first look to ask whether to keep going. It pauses only when a decision genuinely needs you.
- A Grafana link now works as a starting point: it reads the panel filter or the alert's firing condition and investigates the matching logs for you, so you no longer have to turn an alert into a log search yourself.
- When the cause is further down, it keeps following the chain through your own team's services until it reaches where the fault actually starts or crosses into another team's system — there is no longer a fixed two-hop limit.

### Added
- Alerts with no matching error logs (for example a pure CPU or memory spike) no longer dead-end — the investigation switches to checking that service's infrastructure metrics directly.

## [1.4.0] - 2026-07-20

### Changed
- When a service in the call chain responds slowly but is otherwise healthy — no errors of its own, normal CPU and memory — the investigation no longer stops there and blames it. It now recognizes that a slow-but-healthy service is waiting on something further down, and keeps following the dependency chain (using your project/service docs and config to find the next hop) until it reaches the part that actually broke or crosses into another team's system — so you no longer have to hand it the causal chain yourself.

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
