---
name: database-schema-design
description: Database schema design for PostgreSQL/MySQL with normalization, relationships, constraints. Use for new databases, schema reviews, migrations, or encountering missing PKs/FKs, wrong data types, premature denormalization, EAV anti-pattern.
keywords: database schema, schema design, database normalization, 1nf 2nf 3nf,
  primary key, foreign key, database relationships, one to many, many to many,
  data types postgresql, constraints check, audit columns, soft delete,
  database best practices, schema patterns, database anti-patterns,
  missing primary key, no foreign key, varchar max, denormalization,
  entity relationship, composite key, uuid vs bigserial, timestamptz
user-invocable: false
license: MIT
---

# database-schema-design

Schema design and review rules for PostgreSQL and MySQL. Design to 3NF; denormalize only against a measured query, and record the measurement with the decision.

## Rules

| Every table | Why |
|---|---|
| A primary key | Row identity; nothing references a table without one |
| Foreign keys declared, with `ON DELETE` / `ON UPDATE` stated | Referential integrity is the database's job; an implicit default cascade rule is a decision nobody made |
| Every foreign key indexed | Neither engine indexes the referencing side; unindexed FKs are the usual slow JOIN and slow cascade |
| `NOT NULL` on required columns | Optional-by-accident columns leak NULL into every consumer |
| `created_at` / `updated_at` (`TIMESTAMPTZ` on PostgreSQL) | Debugging and compliance need them after the fact, when they cannot be backfilled |
| Bounded types: `VARCHAR(n)` sized to the domain, `DATE`/`TIMESTAMPTZ` for dates, `DECIMAL` for money | An unbounded or wrong-typed column validates nothing and sorts wrong |
| `CHECK` for closed value sets, ranges | Enforced at the one place every writer passes through |

| Reject in review | Why |
|---|---|
| Dates or money as strings | No arithmetic, no validation, broken ordering |
| Missing FK constraints | Orphans, and no way to tell which rows are wrong |
| EAV (entity-attribute-value) tables | No types, no constraints, every query a pivot — model the common attributes as columns and put the genuinely dynamic tail in `JSONB` / `JSON` with a GIN index |
| Polymorphic associations (one FK column, a type discriminator) | The database cannot enforce the reference |
| Circular FK dependencies | Cannot be populated in order; breaks CASCADE |
| Denormalization with no measurement behind it | Update anomalies bought for a speed-up nobody observed |

**MySQL differences that change the DDL:** no `TIMESTAMPTZ` (use `TIMESTAMP`, stored as UTC), no `gen_random_uuid()` (`UUID()` / `CHAR(36)` or `BINARY(16)`), `JSON` instead of `JSONB`.

## Ship the Schema as Reviewable Artifacts

A schema handed over as prose gets misread. Alongside the DDL, produce whichever of these the change warrants — they are what a reviewer actually checks against.

### ERD

A Mermaid `erDiagram` emitted from the schema just designed, never from memory; a many-to-many names its junction table, since an implicit M:N hides the join row's own columns. When the schema already exists in an ORM, generate the diagram rather than hand-write it — a hand-drawn one drifts from the DDL.

### Row-Level Security policies (PostgreSQL)

When the design is multi-tenant or role-scoped, the tenant boundary belongs in the database, not only in application code — an ORM query that forgets a `WHERE org_id = …` leaks across tenants, RLS does not.

Rules: enable RLS on **every** tenant-scoped table (one table missed is the leak); the policy predicate must be index-backed or every query pays a scan; the app must connect as a non-owner role — a table owner and `BYPASSRLS` roles ignore policies entirely, which is how RLS silently does nothing in staging.

### Seed data

Ship a seed script that exercises the constraints, not just the happy path: one row per enum value, a soft-deleted row, a row at each FK boundary, and a case that *should* violate a CHECK (kept commented, as the documented negative test). Seeds must be idempotent — `ON CONFLICT DO NOTHING` / `MERGE` — so re-running them on a shared dev DB is safe.

Official references: [PostgreSQL data types](https://www.postgresql.org/docs/current/datatype.html), [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [MySQL data types](https://dev.mysql.com/doc/refman/8.0/en/data-types.html).
