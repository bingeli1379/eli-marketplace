# Spec-Driven Development

Spec-driven multi-agent development team plugin for Claude Code.

## Plugin Topology (core + language packs)

`sdd` is the **core** plugin: workflow commands, the orchestrator, the architect,
the four cross-cutting reviewers (review/security/performance/qa), technical-writer,
and the universal skills. Every **implementation specialist** ships as an optional
`sdd-<lang>` pack (`sdd-vue`, `sdd-dotnet`, `sdd-python`, `sdd-godot`, `sdd-electron`,
`sdd-database`, `sdd-devops`) bundling that stack's engineer agent + skills. Each
pack declares `dependencies: ["sdd"]`, so installing a pack pulls in core.

- **Dispatch** uses namespaced `subagent_type` (`sdd-vue:vue-engineer`). The Agent
  registry is session-global, so core dispatches pack agents fine. Resolution and
  the **absent-pack fallback** (dispatch `general-purpose` + brief + core skills,
  notify the user) live in `references/agent-routing.md` — the single source of truth.
- **Cross-plugin skill loading** is verified: a pack agent eager-loads core skills
  (`agent-guidelines`, `engineering-checklist`, `test-driven-development`, …) by
  **bare name** in its `skills:` frontmatter — no duplication, no namespacing needed.
  On-demand `Skill` tool loads also work cross-plugin.
- Adding a language = ship a new `sdd-<lang>` pack + register it in the root
  `marketplace.json` + add a row to `references/agent-routing.md`. Core agents and
  workflow skills are untouched.

## Workflow

```
Full:  /setup → /propose → /validate → /apply → /complete
Quick: /quick <description>  (inline analysis → agent dispatch, no spec files)
```

## Repo Topology (single-repo vs multi-repo)

The workflow auto-detects, at the start of `/propose`, `/apply`, `/quick`, and `/complete`, whether cwd is a single git repo or an umbrella folder containing several independent repos. See `references/repo-topology.md` for the detection and per-mode git rules.

- **single-repo** — cwd is inside a git repo. Original behavior: all git ops and `feature-spec/` against that one repo.
- **multi-repo** — cwd is a folder of independent repos. `feature-spec/` (planning artifacts) lives at the umbrella cwd; each task group is bound to one child repo, and its commits run inside that repo. A cross-repo change splits into one group per repo, ordered contract-first; groups in different repos may run in parallel.

`config.yaml` is always a per-project, optional artifact living inside a repo (`<repo>/feature-spec/config.yaml`). `/setup` is per-project — run it inside a repo. Where a touched repo has no config, the workflow scans its code instead.

## Skills (User-Invocable)

| Command | Description |
|---|---|
| `/setup` | Initialize feature-spec directory; two-phase SCAN → BUILD generates `config.yaml` (tool commands + pointer-form architecture baseline). One artifact only. |
| `/propose <description>` | Generate spec artifacts (proposal, design, specs, tasks) for a new change |
| `/validate <change-name>` | Validate spec artifacts against structural and content rules |
| `/quick <description>` | Quick mode — orchestrator analyzes inline, no spec files. Trivial/simple work it implements inline (no dispatch); medium/complex it dispatches agents sequentially. Always followed by a read-only review pass |
| `/review <target> [lens]` | Read-only standalone review by lens (quality/security/performance/e2e/all); auto-detects lens; no edits, no commits |
| `/role [role]` | Become one specialist agent as an interactive persona on the session model (not the agent's sonnet/low); menu if no role given |
| `/apply <change-name>` | Implement tasks using agent team dispatch (no questions asked) |
| `/apply-all [names...]` | Batch apply multiple changes sequentially, unattended |
| `/complete <change-name>` | Complete change: confirm tasks done, delete artifacts, commit cleanup |

## Spec Directory Structure

```
feature-spec/
  config.yaml                # Tool commands + architecture baseline (generated once by /setup, persists; not auto-synced)
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

### Handoff & resume

`tasks.md` (with its `- [x]` checkboxes) **is** the durable handoff/state artifact — no separate state file. A `/apply` run interrupted by a rate limit, a crash, or a handoff to another person resumes from it: Step 5 reconciles `tasks.md` against git history (matching task numbers in commits), re-marks anything already committed, and continues from the first pending group. Because writes are single-writer on one branch, the branch tip + `tasks.md` fully describe progress. `/quick` is **fileless by design** — it writes no `tasks.md`, so a long `/quick` run is not resumable across sessions; if a change is large enough to need cross-session handoff or hand-off to another person, use the spec path (`/propose` → `/apply`) so the durable record exists.

## Agent Definitions

Core agents live in this plugin's `agents/`; pack agents live in their `sdd-<lang>`
plugin's `agents/`. The orchestrator does **not** read these files at dispatch — it
dispatches by `subagent_type` and the harness auto-loads the definition. See
`references/agent-routing.md` for `subagent_type` names, homes, and the fallback.

| Agent | Home | Role |
|---|---|---|
| `orchestrator` | core | Tech Lead — task analysis, agent dispatch, progress tracking |
| `architect` | core | Software Architect — system design, API contracts, integration specs |
| `review-engineer` | core | Code quality — architecture compliance, patterns, performance |
| `security-engineer` | core | Security — OWASP, injection, auth, dependency risks |
| `performance-engineer` | core | Performance — cross-stack (FE Core Web Vitals/bundle, BE API/SP/query), static data-scale capacity review |
| `qa-engineer` | core | QA — Playwright E2E acceptance testing, spec scenario verification |
| `technical-writer` | core | Documentation — API docs, changelogs, README, ADRs |
| `vue-engineer` | `sdd-vue` | Frontend — Vue ecosystem (Nuxt SSR, Vue 3 Vite SPA, Vue 2, single-spa), Atomic Design, Composable Pattern |
| `dotnet-engineer` | `sdd-dotnet` | Backend — ASP.NET (modern .NET Core + legacy .NET Framework), Clean/Layered Architecture, EF Core + Dapper |
| `python-engineer` | `sdd-python` | Backend/ML — FastAPI, data pipelines, ML models, LLM, monitoring |
| `electron-engineer` | `sdd-electron` | Electron — main process, IPC, preload, native OS, packaging |
| `godot-engineer` | `sdd-godot` | Godot — GDScript/C# game dev, scenes, nodes, autoloads, signals, resources, 2D game systems |
| `database-engineer` | `sdd-database` | Database — schema design, migration strategy, query optimization, indexing |
| `devops-engineer` | `sdd-devops` | DevOps — Docker, Kubernetes, CI/CD (GitLab CI / GitHub Actions), infrastructure |

## Bundled Skills

Skills provide domain knowledge that agents reference. **Universal** skills live in
core `skills/`; **stack-specific** skills live in their `sdd-<lang>` pack's `skills/`.
`skills/SOURCES.yaml` (in core) stays the **central registry for all skills across
every pack** and lists their upstream sources.

**When adding a new skill, add its entry to core `skills/SOURCES.yaml`** (even if the
skill file lives in a pack) so `scripts/update-skills.sh` can sync it — the script
resolves each skill's actual home by searching `plugins/*/skills/<name>`. Skills with
`repo: original` are maintained here and not pulled from upstream.

**Skill loading is per-agent and eager.** A subagent's `skills:` frontmatter is injected in full at spawn (not progressive), so each declared skill costs its SKILL.md body on every dispatch (`references/` stay on-demand). To keep dispatches lean, agents declare only **cross-task-universal** skills eagerly and invoke **stack-/datastore-/infra-specific** skills **on demand via the Skill tool** after their Stack Detection step (see database/performance/dotnet/python engineers' "Load skills on demand" sections).

## Development Methodology

- **SDD (Spec-Driven Development)**: `/propose` produces complete specs before any code is written
- **DDD (Domain-Driven Design)**: Domain model (aggregates, value objects, events) defined in `design.md` during propose
- **TDD (Test-Driven Development)**: Frontend and backend agents write unit tests FIRST (Red → Green → Refactor)
- **Contract-First**: API contracts and shared types defined in `design.md` enable parallel frontend/backend development
- **No-guess signaling**: agents never invent facts they don't have. The `NEEDS` / `CONFLICT` / `BLOCKED` vocabulary (defined in `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns*) lets an agent stop on an unobtainable external fact, a spec disagreement, or a genuine blocker; the orchestrator resolves `NEEDS` with whatever tools the environment provides and resumes the same agent with its context intact. sdd defines the protocol, not the lookup tools — keeping the plugin environment-agnostic.

## Implementation Pipeline

```
Phase 1 (sequential single-writer): Groups dispatched one at a time in dependency order,
  each committing on the current branch → in-place squash into one clean commit per group.
  Writes stay single-threaded (no parallel worktrees, no merge step); reads may fan out.
  Multi-repo exception: groups in different child repos may run in parallel.
Phase 2 (parallel read-only review): Code Review + Security Review + QA (+ performance-engineer
  if the diff touches an API/DB surface — advisory, report-only) → sequential fix agents → squash
Phase 3: Documentation
```

## Team Standards

These are the **default** house standards for greenfield code. When a project's existing stack differs (a Vite SPA, legacy .NET Framework, a non-default data store, GitLab CI, etc.), each agent detects and matches the project — see each agent's *Stack Detection First* section.

- **Frontend**: Vue 3 Composition API + Nuxt 4, Atomic Design, Composable Pattern, TailwindCSS, TypeScript strict
- **Backend**: ASP.NET Core .NET 8–10, Clean/Layered Architecture, EF Core + Dapper, Polly, Redis, C# 12–13
- **Game (Godot)**: Godot 4.x, GDScript with static typing (C# when the repo is a .NET project), scene/node composition + loose coupling ("call down, signal up"), data-driven via `Resource`, gdUnit4 tests, gdtoolkit format/lint
- **Unit Tests**: Written by frontend/backend agents themselves (TDD), new code 100% coverage
- **E2E Tests**: Written by QA agent with Playwright, verifies all spec WHEN/THEN scenarios
- **Language**: Traditional Chinese communication, English code and comments
- **Commits**: Each group = one reviewable commit. Final messages follow `conventional-commits` skill (`skills/conventional-commits/SKILL.md`) rules (no task numbers, no attribution blocks)
