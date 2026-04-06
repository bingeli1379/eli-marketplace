## Context

<!-- Background: current state, existing systems, relevant constraints. -->

## Goals / Non-Goals

**Goals:**
<!-- Numbered or bulleted list of what this change aims to achieve. -->

**Non-Goals:**
<!-- Explicitly out-of-scope items to prevent scope creep. -->

## Domain Model (DDD)

<!-- Identify bounded contexts, aggregates, value objects, and domain events. -->
<!-- ### Bounded Contexts -->
<!-- ### Aggregates -->
<!-- - [AggregateName]: root entity, child entities, invariants -->
<!-- ### Value Objects -->
<!-- ### Domain Events -->

## API Contract

<!-- Define the contract between frontend and backend so both can develop in parallel. -->
<!-- For each endpoint: -->
<!-- ### [METHOD] /api/[resource] -->
<!-- **Request**: { field: type } -->
<!-- **Response**: { field: type } -->
<!-- **Status codes**: 200, 400, 404, ... -->
<!-- **Auth**: required/optional -->

## External Boundary Contracts

<!-- Required when this change touches any boundary contract — either direction: -->
<!-- (A) You OWN the boundary and change its contract (an API you expose, event/message schema, shared type, DB column) → list EVERY consumer + how each is kept working (lockstep change / versioning / backward-compat transition). Never break a consumer silently. -->
<!-- (B) You CROSS a boundary you do not own (send a value to a backend/third-party, URL/asset path, cookie) → convert at the boundary to the format the other side expects (anti-corruption layer). -->
<!-- List every boundary/consumer and the decision at each. "No boundary touched" is valid ONLY after tracing the changed contract/value to the wire. -->
<!-- | Boundary / consumer | Direction | Value / contract | External expectation | Decision | -->
<!-- | POST /api/voucher `lang` param | outbound (cross) | Language | backend parses legacy `EN` | convert via `toBackendLanguageType` | -->
<!-- | GET /api/user response, `tier` renamed from `level` | inbound (I own) | tier: string | mobile app v3 still reads `level` | keep both fields one release, then deprecate `level` | -->

## Shared Types

<!-- TypeScript interfaces or C# DTOs that both frontend and backend must agree on. -->
<!-- These serve as the integration contract for parallel development. -->
<!-- ```typescript -->
<!-- interface UserSearchRequest { query: string; page: number; pageSize: number } -->
<!-- interface UserSearchResponse { items: User[]; totalCount: number } -->
<!-- ``` -->

## Data Migration & Rollback

<!-- Required when this change alters persisted data shape: new/renamed/dropped column or table, new index, or a type/format change to stored data. -->
<!-- - **Backfill**: how existing rows are migrated (script, default, lazy) — or state why none is needed. -->
<!-- - **Rollback**: how to revert if the change fails in production (reversible migration, expand-contract, feature flag). -->
<!-- - **Compatibility window**: if old and new code run simultaneously (rolling deploy), how both read/write the data safely. -->
<!-- "No migration needed" is valid ONLY after confirming no existing data is affected. -->

## Affected Files

<!-- Complete inventory of every file that needs to be created, modified, or deleted. -->
<!-- This section is generated from the exhaustive codebase scan in the propose phase. -->
<!-- Every file listed here MUST be covered by at least one task in tasks.md. -->

<!-- ### Files to Create -->
<!-- - `path/to/new-file.ts` — [reason] -->

<!-- ### Files to Modify -->
<!-- - `path/to/existing-file.ts` — [what changes and why] -->

<!-- ### Files to Delete -->
<!-- - `path/to/obsolete-file.ts` — [reason] -->

## Decisions

<!-- For each key decision, use this structure: -->
<!-- ### N. Decision Title -->
<!-- Description of the chosen approach. -->
<!-- **Alternative**: [name] — [why rejected] -->

## Risks / Trade-offs

<!-- Bulleted list: [category] risk description → mitigation or acceptance rationale. -->
