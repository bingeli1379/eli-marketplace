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

### `/write-pr` — Pull / Merge Request Description

Writes the title and description for a pull request or merge request from the branch's commits and diff, as a one-minute briefing for a reviewer.

- Title: Conventional Commits, matching the repo's recent style
- Body sections: Why, What changed, Scope (always, including what it leaves out), Tradeoffs, Blast radius, Verification
- Verification lists only runs that happened; a check that was not run is written `not run`
- Shows the text and stops; it opens the PR or MR only when you ask, with the tool that matches the `origin` remote (`gh`, `glab`, or an MCP for that forge), and never pushes

### `/sharpen` — Sharpen a Task

Rewrites a shallow or vague task prompt so it asks for deeper work, not wider scope. It answers four questions about the task (what a top professional would do that you did not ask, the rawest material to start from, the specific methods and tools, and what other than you or the model would show the result is right), then rewrites the prompt to ask for exactly that.

- Command-only: you invoke it, the model never selects it
- Takes the task as an argument, or your last request when empty
- Rewrites the prompt and stops; it does not do the task
- Choices that are yours stay open in the rewrite instead of being decided

### `/handoff` — Hand the Work to Another Session

Compacts the current session into `HANDOFF.md` at the top of the working directory, so an agent holding none of this conversation can continue the work, and one `rm` clears it when the work lands. For work that has to travel: another window, another repo, another harness, or a side task forked off while this session stays live. Not a replacement for `/compact`, which keeps the same thread.

- Command-only: you invoke it, the model never selects it
- Takes what the next session is for as an argument, and weights the file toward it
- Fixed sections, `已決定不做` among them — a closed decision left out reads as an open task and the next session re-derives it
- `還沒做` and `等你決定` are separate sections: the next session does everything in the first, and leaves the second for you
- Reads the file back as the next session would and fills what that reader would have to ask, up to 3 rounds
- Confirms before replacing an existing `HANDOFF.md`, and offers to `.gitignore` it
