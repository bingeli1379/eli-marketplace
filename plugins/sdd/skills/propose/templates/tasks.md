<!-- Each group = one reviewable unit = one final commit after squash. -->
<!-- Each group contains a single agent type. Group heading describes the concern, not the agent type. -->
<!-- Dependency annotation: <!-- depends: N[, M...] --> on the heading line. Omit if no dependency. -->
<!-- Valid agent tags: Backend, Frontend, Electron, Database, DevOps, Performance, Security, Documentation, E2E -->
<!-- NOTE: Unit tests are included within Backend/Frontend tasks (TDD). E2E tests get their own group. -->

<!-- Example: a "User Search" feature split into reviewable units -->

## 1. Search API and service layer

- [ ] 1.1 (Backend) Write unit test for SearchService (RED)
- [ ] 1.2 (Backend) Implement SearchService to pass test (GREEN)
- [ ] 1.3 (Backend) Add SearchController endpoint with filtering and pagination

## 2. Search page and composables  <!-- depends: 1 -->

- [ ] 2.1 (Frontend) Write unit test for useSearch composable (RED)
- [ ] 2.2 (Frontend) Implement useSearch composable to pass test (GREEN)
- [ ] 2.3 (Frontend) Create SearchPage component with search input and result list

## 3. Search E2E acceptance tests  <!-- depends: 1, 2 -->

- [ ] 3.1 (E2E) Write E2E test for user searches by keyword
- [ ] 3.2 (E2E) Write E2E test for empty search results

<!-- Example: a refactoring change — each group = one type of mechanical operation -->

<!-- ## 1. Remove empty script setup blocks -->
<!-- - [ ] 1.1 (Frontend) Remove empty <script setup> blocks in all components -->

<!-- ## 2. Reorder SFC to script-template-style -->
<!-- - [ ] 2.1 (Frontend) Reorder SFC blocks to script-template-style in all components -->
