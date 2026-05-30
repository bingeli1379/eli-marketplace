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

## Shared Types

<!-- TypeScript interfaces or C# DTOs that both frontend and backend must agree on. -->
<!-- These serve as the integration contract for parallel development. -->
<!-- ```typescript -->
<!-- interface UserSearchRequest { query: string; page: number; pageSize: number } -->
<!-- interface UserSearchResponse { items: User[]; totalCount: number } -->
<!-- ``` -->

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
