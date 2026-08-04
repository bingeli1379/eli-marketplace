# Changelog

## [1.1.1] - 2026-08-04

### Changed
- The pack carries a name in the plugin list and is described as a stack pack, so the sdd family reads as one set rather than separate entries.

## [1.1.0] - 2026-07-25

### Added
- **PostgreSQL depth**: work that touches JSONB columns, GIN/GiST/BRIN indexes, replication and its lag, VACUUM and table bloat, extensions like PostGIS or pgvector, or the `pg_stat_*` views now has a dedicated skill. Ordinary slow-query work still goes to the portable tuning skill.
- **SQL Server diagnosis**: when the instance itself is the suspect — timeouts, blocking, "the server is slow" — there are now ready-to-run queries for wait statistics, the heaviest queries, what is running right now, and who is blocking whom, plus what those numbers do and do not mean (wait totals are cumulative since restart; a query missing from the cache is not an innocent query; an average hides a procedure that is catastrophic for one set of parameters).
- Schema work now also produces the artifacts a reviewer can actually check: an ER diagram, row-level security policies when the design is multi-tenant, and seed data that exercises the constraints instead of the happy path.

### Changed
- Thresholds and settings for SQL Server (index maintenance, tempdb files, MAXDOP, memory) are now looked up in the official documentation and cited, rather than answered from memory — the widely repeated numbers for these are frequently the outdated ones.

## [1.0.2] - 2026-06-24

### Changed
- The database engineer reasons more deeply (higher reasoning effort) for more thorough implementation and review.

## [1.0.1] - 2026-06-22

### Changed
- Sharpened when each SQL skill activates — PostgreSQL/MySQL tuning, SQL Server/Oracle tuning, and query authoring no longer overlap — so the guidance that loads matches your database.

## [1.0.0] - 2026-06-19

### Added
- Initial release. Bundles the database engineer and its database skills, extracted from the sdd core plugin. Install alongside sdd (pulled in automatically as a dependency) to add database support to the spec-driven workflow.
