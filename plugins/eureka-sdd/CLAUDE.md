# Eureka SDD

Spec-driven multi-agent development team plugin for Claude Code.

## Workflow

```
Full:  /esdd-init → /esdd-propose → /esdd-validate → /esdd-apply → /esdd-complete
Quick: /esdd-quick <description>  (inline analysis → agent dispatch, no spec files)
```

## Skills (User-Invocable)

| Command | Description |
|---|---|
| `/esdd-init` | Initialize feature-spec directory; two-phase SCAN → BUILD generates config.yaml + context.md (AI-readable project map) |
| `/esdd-propose <description>` | Generate spec artifacts (proposal, design, specs, tasks) for a new change |
| `/esdd-validate <change-name>` | Validate spec artifacts against structural and content rules |
| `/esdd-quick <description>` | Quick mode — orchestrator analyzes inline and dispatches agents, no spec files |
| `/esdd-apply <change-name>` | Implement tasks using agent team dispatch (no questions asked) |
| `/esdd-apply-all [names...]` | Batch apply multiple changes sequentially, unattended |
| `/esdd-complete <change-name>` | Complete change: extract knowledge, update docs, clean up |
| `/knowledge-audit` | Audit knowledge.md entries against current codebase |

## Spec Directory Structure

```
feature-spec/
  config.yaml                # Tool-runnable config: lint_commands, verification_commands (auto-generated, persists)
  context.md                 # AI-readable project map: layers, domain map, entry points, hard rules (auto-generated, kept in sync by /esdd-complete)
  knowledge.md               # Operational gotchas + dev tips (seeded by /esdd-init, appended by /esdd-complete; persists)
  specs/                     # Accumulated main specs (cleaned up after all changes complete)
    <capability>/spec.md
  changes/
    <name>/
      proposal.md             # What & why
      design.md               # How (domain model, API contract, shared types, decisions)
      tasks.md                # Implementation checklist (grouped by reviewable unit, one agent type per group)
      specs/                  # Delta specs (acceptance criteria)
        <capability>/spec.md
```

After `/esdd-complete`, completed changes are deleted (not archived). Valuable knowledge is extracted to `feature-spec/knowledge.md` (sits next to `context.md`). `config.yaml`, `context.md`, and `knowledge.md` persist; `context.md` is auto-synced (Domain-to-Code Map, Entry Points, Hard Rules, Common Commands) by each `/esdd-complete` run.

## Agent Definitions

Agent role definitions live in `agents/`. The orchestrator reads these at dispatch time.

| Agent | Role |
|---|---|
| `orchestrator` | Tech Lead — task analysis, agent dispatch, progress tracking |
| `architect` | Software Architect — system design, API contracts, integration specs |
| `vue-engineer` | Frontend — Vue 3 / Nuxt 4, Atomic Design, Composable Pattern |
| `dotnet-engineer` | Backend — ASP.NET Core, Clean Architecture, EF Core |
| `python-engineer` | Backend/ML — FastAPI, data pipelines, ML models, LLM, monitoring |
| `review-engineer` | Code quality — architecture compliance, patterns, performance |
| `security-engineer` | Security — OWASP, injection, auth, dependency risks |
| `electron-engineer` | Electron — main process, IPC, preload, native OS, packaging |
| `database-engineer` | Database — schema design, migration strategy, query optimization, indexing |
| `devops-engineer` | DevOps — Docker, Kubernetes, GitHub Actions CI/CD, infrastructure |
| `performance-engineer` | Performance — Core Web Vitals, bundle analysis, API profiling, caching |
| `qa-engineer` | QA — Playwright E2E acceptance testing, spec scenario verification |
| `technical-writer` | Documentation — API docs, changelogs, README, ADRs |

## Bundled Skills

Skills in `skills/` provide domain knowledge that agents can reference. See `skills/SOURCES.yaml` for the full list and upstream sources.

**When adding a new skill, you must also add its entry to `skills/SOURCES.yaml`** so that `scripts/update-skills.sh` can keep it in sync with upstream. Skills with `repo: original` are maintained in this plugin and are not pulled from upstream.

## Shared Templates

Plugin-level templates that are referenced by more than one skill live in `templates/`. Treat each as a single source of truth; skills must read from this directory rather than re-inlining the content.

| Template | Used by |
|---|---|
| `templates/knowledge.md` | `/esdd-init` (initial skeleton), `/esdd-complete` (skeleton when missing) |

## Development Methodology

- **SDD (Spec-Driven Development)**: `/esdd-propose` produces complete specs before any code is written
- **DDD (Domain-Driven Design)**: Domain model (aggregates, value objects, events) defined in `design.md` during propose
- **TDD (Test-Driven Development)**: Frontend and backend agents write unit tests FIRST (Red → Green → Refactor)
- **Contract-First**: API contracts and shared types defined in `design.md` enable parallel frontend/backend development

## Implementation Pipeline

```
Phase 1 (wave-based): Groups dispatched in dependency waves, each in isolated worktree
  → After each wave: merge-squash each group into one clean commit
Phase 2 (parallel): Code Review + Security Review + QA (all 3 simultaneous) → parallel fix agents → squash
Phase 3: Documentation
```

## Team Standards

- **Frontend**: Vue 3 Composition API + Nuxt 4, Atomic Design, Composable Pattern, TailwindCSS, TypeScript strict
- **Backend**: ASP.NET Core .NET 8–10, Clean/Layered Architecture, EF Core + Dapper, Polly, Redis, C# 12–13
- **Unit Tests**: Written by frontend/backend agents themselves (TDD), new code 100% coverage
- **E2E Tests**: Written by QA agent with Playwright, verifies all spec WHEN/THEN scenarios
- **Language**: Traditional Chinese communication, English code and comments
- **Commits**: Each group = one reviewable commit. Final messages follow `conventional-commits` skill (`skills/conventional-commits/SKILL.md`) rules (no task numbers, no attribution blocks)
