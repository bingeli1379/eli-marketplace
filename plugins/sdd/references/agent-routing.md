# Agent Routing

Authoritative map from a task tag / role name to the agent that handles it.
The sdd **core** plugin owns the orchestrator, architect, the four cross-cutting
reviewers, and technical-writer. Every **implementation** specialist ships as an
optional `sdd-<lang>` pack. Packs are NOT guaranteed to be installed — dispatch
tolerates their absence (see *Fallback*).

This file is the single source of truth consumed by `orchestrator.md` (dispatch),
`/quick` (dispatch + inline skill-borrow), and `/role` (persona resolution).

## Routing table

| Task tag | Role name | `subagent_type` | Home | Fallback brief (used only when the pack is absent) |
|---|---|---|---|---|
| — | architect | `sdd:architect` | core | System architect: system design, API contracts, shared types, integration specs. |
| `(Frontend)` | vue-engineer | `sdd-vue:vue-engineer` | sdd-vue | Senior frontend engineer (Vue/Nuxt ecosystem): components, composables, Pinia, styling, FE tests. |
| `(Backend)` | dotnet-engineer | `sdd-dotnet:dotnet-engineer` | sdd-dotnet | Senior ASP.NET backend engineer (.NET Core + legacy .NET Framework): APIs, business logic, EF Core/Dapper, domain models. |
| `(Python)` | python-engineer | `sdd-python:python-engineer` | sdd-python | Senior Python backend/ML engineer: FastAPI, data pipelines, ML integration, DB access, tests. |
| `(Electron)` | electron-engineer | `sdd-electron:electron-engineer` | sdd-electron | Senior Electron engineer: main/preload, IPC, native OS, auto-update, packaging; strict contextIsolation/sandbox. |
| `(Godot)` | godot-engineer | `sdd-godot:godot-engineer` | sdd-godot | Senior Godot game engineer (GDScript-first, C# capable): scenes, nodes, autoloads, signals, resources, 2D systems. |
| `(Database)` | database-engineer | `sdd-database:database-engineer` | sdd-database | Database specialist: schema design, migration strategy, query/index optimization, data integrity across SQL/NoSQL. |
| `(DevOps)` | devops-engineer | `sdd-devops:devops-engineer` | sdd-devops | DevOps engineer: Docker, Kubernetes, CI/CD (GitLab CI / GitHub Actions), infra config, monitoring. |
| `(Performance)` | performance-engineer | `sdd:performance-engineer` | core | — (always present) |
| `(E2E)` | qa-engineer | `sdd:qa-engineer` | core | — (always present) |
| `(Security)` | security-engineer | `sdd:security-engineer` | core | — (always present) |
| `(Documentation)` | technical-writer | `sdd:technical-writer` | core | — (always present) |
| — | review-engineer | `sdd:review-engineer` | core | — (always present) |

## Dispatch protocol (orchestrator, `/quick`, `/apply`)

1. **Resolve** the role to its `subagent_type` via the table.
2. **Dispatch** with the Agent tool using that `subagent_type`. When the pack is
   installed, the harness loads the agent's full definition (system prompt +
   eager `skills:`) automatically — do **not** read or embed the agent file.
3. **Fallback (pack absent).** A `subagent_type` for an uninstalled pack returns a
   catchable tool error (`Agent type '…' not found`). On that error:
   - Dispatch `general-purpose` instead, embedding the **Fallback brief** from the
     table as its role, plus the same task prompt.
   - The pack's stack skills do **not** exist either, so the fallback agent loads
     only **core** universal skills on demand (`engineering-checklist`,
     `test-driven-development`, `clean-architecture`, etc.) — never a `sdd-<pack>:`
     skill.
   - **Tell the user, loudly:** e.g. `⚠️ sdd-vue 未安裝，前端任務改用通用 agent 執行（無 Vue 專屬 skill，品質下降）。建議 /plugin install sdd-vue。` This notice is per-run and live — never cached.
4. Core roles (architect, reviewers, writer) are always present; no fallback path.

## Agent-file resolution (`/role` persona, `/quick` inline skill-borrow)

These two flows read an agent's markdown directly (for the full persona, or to
borrow its `skills:` list). Resolve the file by the role's **Home**:

- **core** → `${CLAUDE_PLUGIN_ROOT}/agents/<role>.md`
- **pack** → the file lives in a sibling plugin; locate it without assuming the
  install layout:
  ```bash
  find ~/.claude/plugins -type f -path "*/<pack>/agents/<role>.md" 2>/dev/null | head -1
  ```
  (e.g. `<pack>=sdd-vue`, `<role>=vue-engineer`). If nothing is found, the pack is
  not installed:
  - `/role` → tell the user `該 specialist 屬於 sdd-<pack>，尚未安裝。請先 /plugin install sdd-<pack> 再 /sdd:role。` and stop.
  - `/quick` inline → skip borrowing pack skills; load only core skills and note the degradation (same spirit as the dispatch fallback).
