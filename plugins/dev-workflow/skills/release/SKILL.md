---
name: release
description: Use when creating a release, bumping a version, generating a changelog, or when the user asks to release or run /release.
---

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
- Each entry: one line describing what changed + why it matters to the user
- Do NOT include commit hashes — they add noise for end users
- Aggressively merge related changes into a single entry
- Aim for **3–7 entries total** per release; if you have more, you're being too granular
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
- Merge related commits into **one entry** (e.g., 5 commits fixing the same form → 1 entry)
- Batch trivial fixes into "Minor bug fixes and stability improvements" if individually uninteresting
- Target **3–7 entries** per release; exceed only for genuinely large releases
- No commit hashes — users don't need them
