# Spec-Driven Development

Spec-driven multi-agent development team plugin for Claude Code.

## Workflow

```
Full:  /init → /propose → /validate → /apply → /complete
Quick: /quick <description>  (inline analysis → agent dispatch, no spec files)
```

## Repo Topology (single-repo vs multi-repo)

The workflow auto-detects, at the start of `/propose`, `/apply`, `/quick`, and `/complete`, whether cwd is a single git repo or an umbrella folder containing several independent repos. See `references/repo-topology.md` for the detection and per-mode git rules.

- **single-repo** — cwd is inside a git repo. Original behavior: all git ops and `feature-spec/` against that one repo.
- **multi-repo** — cwd is a folder of independent repos. `feature-spec/` (planning artifacts) lives at the umbrella cwd; each task group is bound to one child repo, and its worktree/commits run inside that repo. A cross-repo change splits into one group per repo, ordered contract-first.

`config.yaml` is always a per-project, optional artifact living inside a repo (`<repo>/feature-spec/config.yaml`). `/init` is per-project — run it inside a repo. Where a touched repo has no config, the workflow scans its code instead.

## Skills (User-Invocable)

| Command | Description |
|---|---|
| `/init` | Initialize feature-spec directory; two-phase SCAN → BUILD generates `config.yaml` (tool commands + pointer-form architecture baseline). One artifact only. |
| `/propose <description>` | Generate spec artifacts (proposal, design, specs, tasks) for a new change |
| `/validate <change-name>` | Validate spec artifacts against structural and content rules |
| `/quick <description>` | Quick mode — orchestrator analyzes inline and dispatches agents, no spec files |
| `/apply <change-name>` | Implement tasks using agent team dispatch (no questions asked) |
| `/apply-all [names...]` | Batch apply multiple changes sequentially, unattended |
| `/complete <change-name>` | Complete change: confirm tasks done, delete artifacts, commit cleanup |

## Spec Directory Structure

```
feature-spec/
  config.yaml                # Tool commands + architecture baseline (generated once by /init, persists; not auto-synced)
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

After `/complete`, completed changes are deleted (not archived). `config.yaml` persists across changes. The plugin does not generate or maintain `context.md` / `knowledge.md`, and it does not read the project's own docs — `config.yaml` is the single, authoritative project context that `/propose`, `/apply`, and `/quick` consume. Keep its `architecture` block accurate.

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

## Development Methodology

- **SDD (Spec-Driven Development)**: `/propose` produces complete specs before any code is written
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
