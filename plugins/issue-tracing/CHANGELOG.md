# Changelog

## [1.12.1] - 2026-08-23

### Fixed
- The shortcut that follows one request across services is now checked before it is spent. A run could burn a query on a request id that was never a trace id — a per-connection id from the web server, or a random id of the same shape — then read the empty result as "these ids are unrelated" and abandon the shortcut for every remaining service. The shape now rules it out for free where it cannot work, and an empty result is scoped to the one service it came from.
- Whether requests actually failed no longer depends on the log stream carrying searchable status fields. Where it writes only an ordinary access line, that line is read directly, which yields the status, how long each request took, and the calling address — so a report stops saying the request outcome could not be obtained when the answer was one query away.

## [1.12.0] - 2026-08-22

### Changed
- `/issue-tracing` is now the only way to start an investigation. Handing over a Grafana or Kibana link, an alert, a stack trace or a log dump — or simply asking what is erroring — no longer sets the full triage run going on its own: you get an ordinary answer to what you asked, and the structured Root Cause / Impact / How to Resolve / Unknowns report when you ask for it by name.

## [1.11.0] - 2026-08-04

### Added
- The question of what actually triggered an incident is now answered across every deployment of the service, not just the one the alert points at. A service often runs a second deployment for automated traffic, and when a surge lands there the alerted deployment's own volume can be flat or even lower — which used to read as "no surge" and sent the conclusion to the wrong cause. The report now names which deployment carried the increase.
- Runtime settings are looked up instead of inferred from code. That settles two things code alone cannot: whether the behaviour you are looking at is deliberate (a configured delay or throttle, so its slowness is not evidence of anything), and whether the switch that would have prevented the incident is already turned off — usually the real fix.
- An alert's own first-response instruction and its definitions are treated as leads to check rather than facts. They are written for an earlier incident and go stale quietly, so a "scale out first" that your own numbers disprove gets called out instead of repeated back to you as the recommendation.

### Fixed
- Traffic is no longer counted over a window that contains the slowdown. Access logs record a request when it finishes, so a window overlapping the incident leaves out everything still in flight and undercounts arrivals — which made a real surge look like a dip.
- The "is this actually related?" check now covers any number about to be quoted, latency and slow-request share included, and compares proportions rather than raw counts. A service that is slow by design stops being cited as evidence of pressure.

### Changed
- How to Resolve now says when the alert's prescribed action was disproved by the measurements taken during the investigation, and names any preventive setting found switched off, instead of leaving both out of the report.

## [1.10.1] - 2026-08-04

### Fixed
- Missing tooling is named at the start instead of surfacing as an empty result three steps in. Without the Elasticsearch connection the run stops and tells you which server has to be wired; without Grafana a Kibana-only investigation still goes ahead, and says what it cannot reach.
- The skill now starts from the way an alert actually arrives — "查一下這個 alert", "這個錯誤是什麼原因", "這個噴什麼" — rather than only the formal wording.
- Handing over an alert with no URL used to leave the run without a scope. It now asks once; if there genuinely is no URL it rebuilds the scope from the alert's own condition and labels it reconstructed in the report, so you can see the whole investigation inherits that uncertainty.

## [1.10.0] - 2026-08-02

### Added
- Impact now reports each outcome separately instead of a single "failed requests" number: how many failed, how many succeeded but were slow enough to hurt, and how many were unaffected. Slow-but-successful requests previously had nowhere to appear at all, so a login that eventually worked after thirteen seconds read as no impact. Where the logs carry timings, the report also gives the spread — median, worst, and how many landed in each band — with the cut-off chosen from the data rather than guessed in advance.
- When the cause turns out to be shared infrastructure, the report now covers the other services hit by it, not just the one you started from. Blaming a shared layer while naming a single casualty is the first thing anyone reading the report will question. If one of those services could not be counted, the report says the impact figure is a floor and names who is missing from it.
- Investigations that correctly conclude "nothing is wrong" get their own report shape. The old template assumed there was damage to describe, so a run that found only benign noise had to fill it with zeroes; the new one answers the question actually worth answering — why this alert is noisy and how to stop it firing.

### Fixed
- An error count is no longer reported as a failure count. Libraries routinely log an exception before something upstream catches it and returns a perfectly good response, so the two numbers can be completely unrelated — one investigation would have reported 149 errors breaking logout for requests that all succeeded. The request's actual result is now established before anything reaches the report.
- Searching for an exception by its short name no longer comes back empty while the text is sitting right there. A dotted name like `Some.Namespace.SomeException` is stored as a single unit, so asking for the last part of it matches nothing — and nothing about the result tells you the question was wrong. Affects essentially every .NET exception, namespace and logger name.
- A common error pattern can no longer be dismissed from the conclusion on reasoning alone. Anything above the significance threshold now needs a measured comparison to be set aside; without one it is listed as excluded-but-unmeasured, so you can see which part of the conclusion rests on an argument rather than a number.

### Changed
- The confidentiality rule now covers what the investigation produces, not only the skill itself. A real report collects internal hostnames, pod names, internal IPs, customer ids and tokens, so before any of it is written to a file the destination's visibility has to be established — writing it into an open repository is the easy mistake.

## [1.9.1] - 2026-08-02

### Fixed
- A service is no longer reported as missing from a log stream while it is sitting right there. Whether a service appeared was judged from a sample of recent lines, which on a busy stream is filled by whichever service talks most — so a quieter service could be declared absent even with tens of thousands of lines in the same window. It is now checked by counting that service directly.
- A shared-infrastructure outage is no longer pinned on one service. The "is this hitting many services or only this one?" check was read off that same kind of sample, so a loud caller could hide the other victims, the answer came back "only this one", and the report blamed a downstream service instead of the shared database, cache or network everything was waiting on.
- Investigations no longer stall partway through. One step could fire more queries at once than the log backend accepts; past that limit the requests are not refused, they simply never come back, leaving the investigation waiting indefinitely.

## [1.9.0] - 2026-08-02

### Added
- The whole call chain behind one failing request now comes back in a single lookup, where your logs carry an id shared across services, instead of one lookup per service. It also works when you start from an ordinary log URL — the request id on that log line is matched to the shared id — so the faster path is available from the entry point you already use, not only from a tracing tool.
- Investigations now work on logs that name things differently. Which field holds the service, the environment, the severity, the message text and the timestamp is read from your own environment notes instead of assumed, so a service whose logs land in a second stream under a different naming scheme no longer reads as "no data".

### Fixed
- A trail that simply runs out is no longer reported as the cause. When the last service you can see is where your logging coverage ends rather than where the fault began, the report says that, instead of blaming whichever service happened to be last.
- Reports no longer repeat credentials found in log text. A failed sign-in can log the entire token, and that value used to travel into the report word for word; it is now described by type and left out.
- Incident times are now correct on logs that store the timestamp in an unusual format. Such a window could previously come out wrong by years, or print as a raw number.
- A dashboard panel's "ignore this known noise" filters are now carried into the investigation, and checked that they actually applied — so the error reported as most common is not counted over noise the panel was deliberately hiding.

## [1.8.0] - 2026-07-31

### Added
- Infra checks now catch a single overloaded instance hiding behind a healthy-looking average. One pod can be starved for CPU while every instance's average reads normal and autoscaling never reacts — the report now measures each instance separately and says so when that is what happened.
- When a timeout looks like a slow database or cache, the investigation now checks the caller's own health first. A starved caller produces exactly the same symptom, so this stops the report from sending you to the database or network team over a problem on your own side.

### Fixed
- Searches that quietly returned "0 results" for data that was actually there. One query shape silently emptied the results with no error, which read as "this does not exist" and could end an investigation on the wrong answer — it is no longer used.
- Metric queries that failed with a confusing parse error, and dashboard lookups rejected outright, both caused by wrong parameter names.

## [1.7.1] - 2026-07-23

### Changed
- When chasing a slow-but-not-erroring service, the tool now confirms the exact log field names and types from the log source before searching — so it stops wasting attempts on searches that quietly return nothing (a wrong guess at a path, status, or severity field).

## [1.7.0] - 2026-07-23

### Added
- When a service is slow but not erroring, the investigation now pulls up the slowest requests directly by the response-time number (biggest first) — giving you the count, the worst offenders, and which endpoints are affected in one shot, instead of a text search that quietly comes back empty.

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
