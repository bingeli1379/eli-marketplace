---
name: release
description: Use when creating a release, bumping a version, generating a changelog, or when the user asks to release or run /release.
---

# Release Changelog & Version Bump

**Type**: Automated release workflow
**Goal**: Detect current version, compare changes since that version, generate changelog, and bump version number

## Instructions

### 1. Resolve target & detect version source

**Target package** (multi-package repos): if `$ARGUMENTS` names a package/plugin, that is the release target. Otherwise detect candidate packages (each directory carrying its own version manifest). If exactly one exists, use it. If several exist (e.g. a marketplace with multiple plugins), list them with their current versions and ask which to release — never release all of them at once unless explicitly told.

**Sweep for other changed packages.** When the user asks to also release changed sub-packages ("release the changed ones too") — or after releasing the primary target — detect **every** package that has unreleased changes and release each as its OWN target (own version bump, own CHANGELOG, own `chore(<pkg>): release` commit — never fold several packages into one). Detect per package:
- find its last release commit: `git log --oneline -1 --grep='release v' -- <package>/<version-file>`
- list non-release commits touching it since: `git log <rel>..HEAD --oneline --no-merges -- <package>/`
- a package with commits there has unreleased work; a package with none is up to date, skip it.
Note a single change can land under a package via a commit whose scope tag names a *different* package (see step 3) — path-filtering by `-- <package>/` is what catches it, not the commit message.

Within the target package's directory, search for version files in this priority order. Stop at the first match:

| Source | File | Field / Pattern |
|--------|------|-----------------|
| Plugin manifest | `.*-plugin/plugin.json` (e.g. `.claude-plugin/`, `.codex-plugin/`) | `"version": "x.y.z"` |
| npm / Node.js | `package.json` | `"version": "x.y.z"` |
| .NET | `*.csproj`, `Directory.Build.props` | `<Version>x.y.z</Version>` or `<PackageVersion>` |
| Python | `pyproject.toml` | `version = "x.y.z"` |
| Rust | `Cargo.toml` | `version = "x.y.z"` |
| Go | `version.go` or constant | `const Version = "x.y.z"` |
| Plain | `version.txt`, `VERSION` | raw semver string |

- If no version file is found, check git tags (`git tag --sort=-v:refname`) as fallback
- If nothing is found, ask the user where the version lives

**Parallel manifests (same artifact, multiple files):** one logical package may declare its version in several sibling manifests — e.g. a plugin that ships both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Glob for ALL of them (`<package>/.*-plugin/plugin.json`) and treat them as ONE version source that must move together. They may currently be out of sync (one lagging behind); the release re-syncs them all to the new version. Use the highest existing version among them as the current baseline. This lockstep applies ONLY within the chosen target package — manifests belonging to *different* packages are independent and must never be bumped together.

Record: **current version**, **all version file paths** (every parallel manifest), **field location**

### 2. Find the previous version baseline

Use the following strategy to determine what changed since the last release:

1. **Git log of the version file**: `git log --oneline -10 -- <version-file>` — find the commit that last changed the version, use it as baseline
2. **CHANGELOG.md**: parse the most recent `## [x.y.z]` heading to find the last documented version
3. **Git tags**: if tags exist, find the latest semver tag before the current version
4. **If none works**: show the last 30 commits and ask the user to pick a baseline

Once the baseline commit is identified, scope every range query **to the target package's path**. In a multi-package repo, merges from other feature branches pollute an unfiltered `<baseline>..HEAD` range with unrelated commits (other plugins, other features) — the changelog must be built from the package-scoped list only:
- `git log <baseline>..HEAD --oneline -- <package>/` for the commit list
- `git diff <baseline>..HEAD --stat -- <package>/` for the change summary

Prefer a package-path baseline (`git log --oneline -1 --grep='release v' -- <package>/<version-file>`) over a bare version tag when the history contains merges — a tag can sit on a tangled topology where `tag..HEAD` sweeps in unrelated branches. Grep for `release v` (the `release vX.Y.Z` message pattern), NOT a bare `release` — a feature commit whose message merely mentions "release" (e.g. "harden the release flow") would otherwise be picked as the baseline.

### 3. Categorize changes

- Categorize commits by Conventional Commits type (feat, fix, refactor, etc.)
- If commits don't follow Conventional Commits, infer category from the diff content
- Ignore merge commits and chore/ci/style commits unless they are user-facing
- **A commit's scope tag is not its only package.** One commit may touch several packages (e.g. a `fix(sdd)` commit that also edits an `sdd-electron` agent). Attribute each change to the package whose files it modifies — when releasing package A, the changelog covers only hunks under `A/`; hunks under `B/` belong to B's release. Determine the bump for A from A's path-scoped commits only, not from the commit's scope tag.

### 4. Determine version bump

- **major**: any commit contains `BREAKING CHANGE` or `!` after type
- **minor**: any `feat` commit
- **patch**: only `fix`, `perf`, `refactor`, or other non-feature changes
- Compute the new number from the current version: major → `(x+1).0.0`, minor → `x.(y+1).0`, patch → `x.y.(z+1)`
- **Pre-1.0 (`0.y.z`)**: shift down one level — a breaking change bumps minor (`0.(y+1).0`), a `feat` bumps patch (`0.y.(z+1)`). Never auto-promote a `0.x` package to `1.0.0`; do that only if the user explicitly asks
- Apply the suggested bump automatically without asking for confirmation

### 5. Generate changelog entry

- Format: [Keep a Changelog](https://keepachangelog.com/) style
- Sections: Added, Fixed, Changed, Removed (only include non-empty sections)
- Each entry: one line describing what changed + why it matters to the user
- Do NOT include commit hashes — they add noise for end users
- Aggressively merge related changes into a single entry
- Aim for **3–7 entries total** per release; if you have more, you're being too granular
- Date: use today's date (YYYY-MM-DD)
- Prepend the new entry to the **target package's** `CHANGELOG.md` — the one alongside its version manifest (e.g. `plugins/<name>/CHANGELOG.md`), NOT the repo root. Create if not exists, keep existing entries

### 6. Bump version number

- Update the version field in the detected version file(s)
- **Parallel manifests of the same package** (e.g. `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`) MUST all be bumped to the same new version in lockstep — do NOT ask which to update, update every one
- Only ask the user when the files are **genuinely independent artifacts** (different packages with their own version lifecycles), not when they are mirror manifests of one package
- Preserve each file's existing formatting
- After editing, verify each JSON manifest still parses (e.g. `python3 -m json.tool <file> >/dev/null`) before committing — a version edit that breaks the manifest ships a broken plugin, worse than a stale version

### 7. Commit

- Show the changelog entry and version diff, then immediately commit without waiting for user confirmation
- Stage and commit all release changes (the target's CHANGELOG + version file(s)) with a conventional commit message
- In a multi-package repo, scope the commit to the released package: `chore(<package>): release vX.Y.Z`

## Changelog Format
```markdown
## [x.y.z] - YYYY-MM-DD

### Added
- Short description of what's new — what this means for you

### Fixed
- Short description of what was broken — how it behaves now

### Changed
- Short description of what's different — what you need to do (if anything)

### Removed
- Short description of what's gone — what to use instead (if applicable)
```

## Rules

### Voice & audience
- Write for **end users who don't read code** — describe behavior, not implementation
- Use plain language; avoid jargon like "refactor", "migrate", "normalize"
- Each entry answers: "What changed, and why should I care?"
- English, imperative mood

### What to include
- Only changes the user will **notice or need to act on**
- If a change has no visible effect, it doesn't belong in the changelog

### What to omit (silently)
- Internal refactors, code reorganization, renaming
- Dependency bumps (unless they fix a user-visible bug or add a feature)
- CI/CD, build, lint, style, test-only changes
- Documentation-only changes (unless it's a new user-facing guide)

### Compression
- **Be as concise as possible WITHOUT distorting meaning** — trim filler, but never at the cost of accuracy. A shorter entry that misstates or over-generalizes what changed is worse than a longer, correct one. When concision and fidelity conflict, fidelity wins
- Merge related commits into **one entry** (e.g., 5 commits fixing the same form → 1 entry)
- Batch trivial fixes into "Minor bug fixes and stability improvements" if individually uninteresting
- Target **3–7 entries** per release; exceed only for genuinely large releases
- No commit hashes — users don't need them
