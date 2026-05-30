# Spec-Driven Development

Claude Code plugin — spec-driven multi-agent development team for Vue/Nuxt + ASP.NET projects.

Combines **SDD** (Spec-Driven Development), **DDD** (Domain-Driven Design), and **TDD** (Test-Driven Development) into an automated pipeline.

## Workflow

```
/esdd-init → /esdd-propose (auto-validate) → /esdd-apply → /esdd-complete
```

1. **Init** — auto-detect project context, create `feature-spec/` directory
2. **Propose** — clarify requirements and define feature boundaries, dispatch architect for design, generate specs (SDD), domain model (DDD), API contract, tasks (TDD structure). Auto-validates and fixes until all checks pass.
3. **Apply** — launch named orchestrator agent to dispatch agent team in parallel, review, and verify. User can interact with orchestrator anytime.
4. **Archive** — extract knowledge, update docs, delete change artifacts

## Prerequisites

Enable Agent Teams (required for multi-agent dispatch):

```jsonc
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Usage

### 1. Initialize (once per project)

```
/esdd-init
```

Two-phase: SCAN (auto-detects tech stack, layers, domains; asks up to 3 confirmation questions) then BUILD (writes `feature-spec/config.yaml` for tool commands and `feature-spec/context.md` — an AI-readable project map covering architecture layers, domain-to-code map, entry points, cross-cutting concerns, hard rules, and common commands so AI knows *where* to make changes). `context.md` is auto-synced by `/esdd-complete`.

### 2. Propose a change

```
/esdd-propose add user search feature for admin dashboard
```

Creates `feature-spec/changes/add-user-search/` with:
- `proposal.md` — what & why
- `design.md` — how (domain model, API contract, shared types, decisions)
- `specs/<capability>/spec.md` — acceptance criteria (WHEN/THEN)
- `tasks.md` — TDD-structured implementation checklist

Automatically validates and fixes all artifacts before completion.

### 3. Implement

```
/esdd-apply add-user-search
```

The orchestrator dispatches agents through a 3-phase pipeline:

```
Phase 1 (parallel): Wave-based development in isolated worktrees (TDD)
Phase 2 (parallel): Code Review + Security Review + QA (all 3 simultaneous) → parallel fix agents
Phase 3:            Documentation
```

No questions asked — specs are the single source of truth.

### 3b. Batch implement (optional)

```
/esdd-apply-all add-user-registration add-user-profile add-user-roles
```

Runs `/esdd-apply` on each change sequentially. Confirm execution order once, then unattended. Failed changes are skipped and reported at the end.

### 4. Complete & Extract Knowledge

```
/esdd-complete add-user-search
```

Extracts valuable domain knowledge and dev tips to `feature-spec/knowledge.md`, updates project docs (CLAUDE.md, README), reviews related knowledge for staleness, then deletes the change artifacts. `feature-spec/config.yaml`, `feature-spec/context.md`, and `feature-spec/knowledge.md` persist across changes.

### 5. Audit Knowledge (periodic)

```
/knowledge-audit
```

Verifies every entry in `feature-spec/knowledge.md` against the current codebase. Flags stale or outdated entries for review.

## Agents

Agent role definitions live in [`agents/`](agents/). The orchestrator reads these at dispatch time.

## Skill Updates

Update all bundled skills from upstream:

```bash
./scripts/update-skills.sh          # update all non-frozen skills
./scripts/update-skills.sh --all    # include frozen skills
./scripts/update-skills.sh vue      # update a specific skill
```

All skill sources are tracked in `skills/SOURCES.yaml`. **When adding a new skill, you must also add its entry to `SOURCES.yaml`** so that `update-skills.sh` can keep it in sync with upstream.

See `skills/` for the full list of bundled skills.

## Development Methodology

| Phase | Methodology | What Happens |
|---|---|---|
| Propose | **SDD** | Specs written before code — WHEN/THEN acceptance criteria |
| Propose | **DDD** | Domain model defined — aggregates, value objects, events |
| Propose | **Contract-First** | API contract + shared types enable parallel development |
| Apply | **TDD** | Frontend/backend write unit tests FIRST (Red → Green → Refactor) |
| Apply | **E2E** | QA writes Playwright tests from specs, runs after implementation |

## Spec Directory Structure

```
feature-spec/
  config.yaml               # Tool-runnable config: lint + verification commands (persists)
  context.md                # AI-readable project map (persists, auto-synced by /esdd-complete)
  knowledge.md              # Operational gotchas + dev tips (persists, appended by /esdd-complete)
  changes/
    <name>/
      proposal.md            # What & why
      design.md              # How (domain model, API contract, shared types, decisions)
      tasks.md               # TDD-structured implementation checklist
      specs/                 # Delta specs (acceptance criteria)
        <capability>/spec.md
```

After `/esdd-complete`, change artifacts are deleted. Knowledge is extracted to `feature-spec/knowledge.md` (alongside `context.md` and `config.yaml`).

## Customization

- Edit `agents/` to adjust role definitions, tech stack, or coding standards
- Edit `skills/propose/templates/` to customize artifact templates
- Edit `feature-spec/config.yaml` in your project to set project-specific context and rules

## Credits

Upstream skill sources and their repo URLs are listed in [`skills/SOURCES.yaml`](skills/SOURCES.yaml).
