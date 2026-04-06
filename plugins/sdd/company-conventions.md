# Company Conventions

Company-specific workflow overrides. These are **not** part of the core sdd methodology — they reflect internal team habits and can be removed entirely by deleting this file and its references.

## Pre-lint Skip Rules

| Condition | Action |
|---|---|
| Project tech stack includes ASP.NET / .NET (detected via `.csproj`, `.sln`, or `config.yaml` context) | Skip pre-lint step and skip `lint_commands` in agent prompts |

When a skip rule matches:
- **setup**: Do not generate `lint_commands` entries for the matched tooling (e.g., skip `dotnet format`)
- **apply / quick**: Skip the pre-lint commit step entirely. Do not include `lint_commands` in agent prompt templates. Agents commit without running lint.
