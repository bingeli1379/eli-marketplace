---
name: release
description: "Use when cutting a release, bumping a version, or generating a changelog — or whenever the user asks to release in ANY phrasing: \"release\", \"release 一下\", \"幫我 release\", \"發版\", \"bump 版本\", \"更新 changelog\", or runs /release. Applies even when the bump looks trivial enough to hand-edit the version file — do not hand-roll the version or changelog, invoke this skill. A complaint ABOUT a skill named /release is not this skill; that is a request to improve that skill, not to cut a release."
---

# Release Changelog & Version Bump

**Type**: Automated release workflow
**Goal**: Detect current version, compare changes since that version, generate changelog, and bump version number

**Ask only when the answer is not in the repo** — which package to release, where the version lives when no manifest or tag says, which baseline when none can be found. Everything the repo already settles — the bump, mirror manifests, the commit — is applied without confirmation.

## Instructions

### 1. Resolve target & detect version source

**Target package** (multi-package repos): if `$ARGUMENTS` names a package/plugin, that is the release target. Otherwise detect candidate packages (each directory carrying its own version manifest). If exactly one exists, use it. If several exist (e.g. a marketplace with multiple plugins), list them with their current versions and ask which to release — never release all of them at once unless explicitly told.

**Sweep for other changed packages.** When the user asks to also release changed sub-packages ("release the changed ones too") — or after releasing the primary target — detect **every** package that has unreleased changes and release each as its OWN target (own version bump, own CHANGELOG, own `chore(<pkg>): release` commit — never fold several packages into one). Detect per package:
- find its last release commit: `git log --oneline -1 --grep='release v' -- <package>/` — filter by the package **directory**, not its version file: a first release keeps the version as it stands, so its release commit touches only the CHANGELOG and a version-file filter misses it entirely
- list non-release commits touching it since: `git log <rel>..HEAD --oneline --no-merges -- <package>/`
- a package with commits there has unreleased work; a package with none is up to date, skip it.
Note a single change can land under a package via a commit whose scope tag names a *different* package (see step 3) — path-filtering by `-- <package>/` is what catches it, not the commit message.

**Version source.** Within the target package's directory, find the file that carries its version — a plugin manifest (`.*-plugin/plugin.json`), a language manifest (`package.json`, `*.csproj` / `Directory.Build.props`, `pyproject.toml`, `Cargo.toml`, a `version.go` constant), or a plain `VERSION` / `version.txt`. When a plugin manifest and a language manifest sit side by side, the plugin manifest is the version that ships. No version file → fall back to git tags (`git tag --sort=-v:refname`); nothing there either → ask the user where the version lives.

**Parallel manifests (same artifact, multiple files):** one logical package may declare its version in several sibling manifests — e.g. a plugin that ships both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Glob for ALL of them (`<package>/.*-plugin/plugin.json`) and treat them as ONE version source that must move together. They may currently be out of sync (one lagging behind); the release re-syncs them all to the new version. Use the highest existing version among them as the current baseline. This lockstep applies ONLY within the chosen target package — manifests belonging to *different* packages are independent and must never be bumped together.

Record: **current version**, **all version file paths** (every parallel manifest), **field location**

### 2. Find the previous version baseline

**First, settle whether there is a previous release at all** — every baseline source below assumes one, and each will manufacture a false baseline when there is none. It is a first release when no `release v` commit for the package exists AND no tag names an earlier version AND `CHANGELOG.md` either does not exist or its newest heading already equals the version on disk. **Look for that commit, not for a change to the version file** — a first release that kept the version as it stands leaves the manifest untouched, so every later release of that package would otherwise re-detect it as never released and replay its whole history into the changelog. Then the range is the whole of the package's history, step 4 (determine version bump) keeps the version as it stands, and nothing is asked — there is no earlier version for the user to pick. **Check this before reading the changelog heading in particular**: a first release's newest changelog heading IS the current version, so it would report a baseline equal to what is being released.

Otherwise the baseline is the package's last release commit: `git log --oneline -1 --grep='release v' -- <package>/`. Filter by the package **directory** (the reason step 1 gives), and grep for `release v` (the `release vX.Y.Z` message pattern), NOT a bare `release` — a feature commit whose message merely mentions "release" (e.g. "harden the release flow") would otherwise be picked as the baseline. Prefer this over a bare version tag when the history contains merges — a tag can sit on a tangled topology where `tag..HEAD` sweeps in unrelated branches. When no release commit exists, fall back to the most recent `## [x.y.z]` heading in `CHANGELOG.md`, then to the latest semver tag before the current version; when none settles it, show the last 30 commits and ask the user to pick a baseline.

Once the baseline commit is identified, scope every range query **to the target package's path**. In a multi-package repo, merges from other feature branches pollute an unfiltered `<baseline>..HEAD` range with unrelated commits (other plugins, other features) — the changelog must be built from the package-scoped list only:
- `git log <baseline>..HEAD --oneline -- <package>/` for the commit list
- `git diff <baseline>..HEAD --stat -- <package>/` for the change summary

### 3. Categorize changes

- Categorize commits by Conventional Commits type (feat, fix, refactor, etc.)
- If commits don't follow Conventional Commits, infer category from the diff content
- Ignore merge commits and chore/ci/style commits unless they are user-facing
- **A commit's scope tag is not its only package.** One commit may touch several packages (e.g. a `fix(sdd)` commit that also edits an `sdd-electron` agent). Attribute each change to the package whose files it modifies — when releasing package A, the changelog covers only hunks under `A/`; hunks under `B/` belong to B's release. Determine the bump for A from A's path-scoped commits only, not from the commit's scope tag.

### 4. Determine version bump

- Bump per Conventional Commits: `BREAKING CHANGE` or `!` after type → major `(x+1).0.0`; any `feat` → minor `x.(y+1).0`; otherwise patch `x.y.(z+1)`
- **Pre-1.0 (`0.y.z`)**: shift down one level — a breaking change bumps minor (`0.(y+1).0`), a `feat` bumps patch (`0.y.(z+1)`). Never auto-promote a `0.x` package to `1.0.0`; do that only if the user explicitly asks
- **A package that has never been released does not get bumped.** When step 2 (find the previous version baseline) took its never-released branch, the version on disk *is* this release: keep it, bring the changelog entry up to what actually ships, and commit `chore(<pkg>): release vX.Y.Z` at that same number. Bumping instead assigns a version to work that was never published, and leaves a gap nobody can install.

### 5. Generate changelog entry

- Format: [Keep a Changelog](https://keepachangelog.com/) style — `## [x.y.z] - YYYY-MM-DD` (today's date), sections Added / Fixed / Changed / Removed, only non-empty ones
- Each entry: one line describing what changed + why it matters to the user
- Merge related changes into a single entry (e.g. 5 commits fixing the same form → 1 entry); batch trivial fixes into "Minor bug fixes and stability improvements" if individually uninteresting. Aim for **3–7 entries total** per release; exceed only for genuinely large releases
- No commit hashes — they add noise for end users
- Prepend the new entry to the **target package's** `CHANGELOG.md` — the one alongside its version manifest (e.g. `plugins/<name>/CHANGELOG.md`), NOT the repo root. Create if not exists, keep existing entries

### 6. Bump version number

- Update the version field in the detected version file(s)
- **Parallel manifests of the same package** (e.g. `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`) are all bumped to the same new version in lockstep, every one of them
- Preserve each file's existing formatting
- After editing, verify each JSON manifest still parses (e.g. `python3 -m json.tool <file> >/dev/null`) before committing — a version edit that breaks the manifest ships a broken plugin, worse than a stale version
- **Refresh any lock file that records the package's own version.** Some lock files pin the package being released, not just its dependencies (`package-lock.json` does) — grep the **old** version string in each lock file inside the package, **and in the workspace root's lock file** when the package is a workspace member: an npm/pnpm workspace keeps one lock at the root recording every member's version, so a package-scoped look finds nothing and the stale entry ships. A hit means the lock may carry the package's own version, so refresh it with the ecosystem's metadata-only command (`npm install --package-lock-only` and its equivalents) and confirm the lock now names the **new** version. Do NOT verify by the old string disappearing — an unrelated dependency pinned at that same version keeps it present forever. No such command available → say so and release without it rather than hand-editing the lock

### 7. Commit

- Show the changelog entry and version diff, then commit
- Stage and commit all release changes (the target's CHANGELOG + version file(s) + any lock file refreshed in step 6) with a conventional commit message
- In a multi-package repo, scope the commit to the released package: `chore(<package>): release vX.Y.Z`

## Changelog rules

- Write for **end users who don't read code** — describe behavior, not implementation; plain language, no jargon like "refactor", "migrate", "normalize"; English, imperative mood
- Each entry answers: "What changed, and why should I care?" — only changes the user will **notice or need to act on**
- Omit silently: internal refactors and renames, dependency bumps (unless they fix a user-visible bug or add a feature), CI/CD, build, lint, style, test-only changes, documentation-only changes (unless it's a new user-facing guide)
- **Be as concise as possible WITHOUT distorting meaning** — trim filler, but never at the cost of accuracy. A shorter entry that misstates or over-generalizes what changed is worse than a longer, correct one. When concision and fidelity conflict, fidelity wins
