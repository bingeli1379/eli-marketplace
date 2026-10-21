# dev-workflow

Daily workflow skills for Claude Code.

## Skills

### `/commit` — Commit Message Generation

Inspects staged changes and generates a [Conventional Commits](https://www.conventionalcommits.org/) message, then executes the commit automatically.

- Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `build`
- Title: imperative mood, lowercase, under 50 chars, no period
- Body: explains "what" and "why", wraps at 72 chars, skipped for self-explanatory changes

### `/release` — Release Changelog & Version Bump

Detects the current version from project files (package.json, csproj, pyproject.toml, etc.), compares changes since the last release, generates a [Keep a Changelog](https://keepachangelog.com/) entry, bumps the version, and commits.

- Auto-determines bump level: major (breaking), minor (feat), patch (fix/refactor)
- Changelog written from end-user perspective
- Internal refactors, CI tweaks, dependency bumps are omitted unless user-facing

### `/sharpen` — Sharpen a Task

Rewrites a shallow or vague task prompt so it asks for deeper work, not wider scope. It answers four questions about the task (what a top professional would do that you did not ask, the rawest material to start from, the specific methods and tools, and what other than you or the model would show the result is right), then rewrites the prompt to ask for exactly that.

- Command-only: you invoke it, the model never selects it
- Takes the task as an argument, or your last request when empty
- Rewrites the prompt and stops; it does not do the task
- Choices that are yours stay open in the rewrite instead of being decided
