# Release Changelog & Version Bump

**Type**: Automated release workflow
**Goal**: Detect current version, compare changes since that version, generate changelog, and bump version number

## Instructions

### 1. Detect version source

Search the project root for version files in this priority order. Stop at the first match:

| Source | File | Field / Pattern |
|--------|------|-----------------|
| npm / Node.js | `package.json` | `"version": "x.y.z"` |
| .NET | `*.csproj`, `Directory.Build.props` | `<Version>x.y.z</Version>` or `<PackageVersion>` |
| Python | `pyproject.toml` | `version = "x.y.z"` |
| Rust | `Cargo.toml` | `version = "x.y.z"` |
| Go | `version.go` or constant | `const Version = "x.y.z"` |
| Plain | `version.txt`, `VERSION` | raw semver string |

- If no version file is found, check git tags (`git tag --sort=-v:refname`) as fallback
- If nothing is found, ask the user where the version lives

Record: **current version**, **version file path**, **field location**

### 2. Find the previous version baseline

Use the following strategy to determine what changed since the last release:

1. **Git log of the version file**: `git log --oneline -10 -- <version-file>` — find the commit that last changed the version, use it as baseline
2. **CHANGELOG.md**: parse the most recent `## [x.y.z]` heading to find the last documented version
3. **Git tags**: if tags exist, find the latest semver tag before the current version
4. **If none works**: show the last 30 commits and ask the user to pick a baseline

Once the baseline commit is identified, run:
- `git log <baseline>..HEAD --oneline` for commit list
- `git diff <baseline>..HEAD --stat` for change summary

### 3. Categorize changes

- Categorize commits by Conventional Commits type (feat, fix, refactor, etc.)
- If commits don't follow Conventional Commits, infer category from the diff content
- Ignore merge commits and chore/ci/style commits unless they are user-facing

### 4. Determine version bump

- **major**: any commit contains `BREAKING CHANGE` or `!` after type
- **minor**: any `feat` commit
- **patch**: only `fix`, `perf`, `refactor`, or other non-feature changes
- Apply the suggested bump automatically without asking for confirmation

### 5. Generate changelog entry

- Format: [Keep a Changelog](https://keepachangelog.com/) style
- Sections: Added, Fixed, Changed, Removed (only include non-empty sections)
- Each entry: one line per change, optionally reference commit hash for significant changes
- Date: use today's date (YYYY-MM-DD)
- Prepend the new entry to `CHANGELOG.md` (create if not exists, keep existing entries)

### 6. Bump version number

- Update the version field in the detected version file(s)
- If multiple version files exist, ask the user which to update
- Preserve the file's existing formatting

### 7. Commit

- Show the changelog entry and version diff, then immediately commit without waiting for user confirmation
- Stage and commit all release changes (CHANGELOG.md, version file(s)) with a conventional commit message

## Changelog Format
```markdown
## [x.y.z] - YYYY-MM-DD

### Added
- description (commit-hash)

### Fixed
- description (commit-hash)

### Changed
- description (commit-hash)

### Removed
- description (commit-hash)
```

## Rules
- Write from the end-user's perspective: describe **what changed**, not how it was implemented
- Only include changes the user will actually notice or care about
- Skip or omit: internal refactors, dependency bumps, CI tweaks, code style changes — unless they affect user-facing behavior
- Condense minor fixes into a single line (e.g., "minor bug fixes") rather than listing each one
- Group related commits into a single entry
- Write in English, imperative mood
- Keep entries concise — one line per change, fewer entries is better
