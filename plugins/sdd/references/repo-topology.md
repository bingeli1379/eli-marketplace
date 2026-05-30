# Repo Topology

Shared rules for how the sdd workflow adapts to **single-repo** vs **multi-repo** working directories. `/propose`, `/apply`, `/quick`, and `/complete` load this file at Step 0 and follow it. The single-repo path is the original behavior and must stay unchanged; multi-repo is the added mode.

---

## Step 0 — Detect topology (run once, at the start)

Run from the current working directory (cwd):

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$ROOT" ]; then
  echo "single-repo"        # cwd is inside a git repo → operate on that repo
else
  # cwd is not in any git repo → look for child repos (immediate children only)
  CHILD_REPOS=$(for d in */; do [ -e "${d%/}/.git" ] && echo "${d%/}"; done)
  if [ -n "$CHILD_REPOS" ]; then echo "multi-repo"; else echo "no-git"; fi
fi
```

- **single-repo** — cwd is within a git repo (at its root or below). The original mode. Everything (git ops, `feature-spec/`) happens against that one repo.
- **multi-repo** — cwd is NOT in a git repo, but has one or more immediate child directories that are git repos. Each child repo is an independent project; a change may span several of them.
- **no-git** — cwd is not in a repo and has no child repos. Proceed read-only where possible; warn that git-dependent steps (worktree, commit) cannot run.

Child-repo detection is **immediate children only** — nested repos deeper in the tree are out of scope. Announce the detected mode (and, in multi-repo, the list of child repos) before proceeding.

---

## Where `feature-spec/` lives

Always at **cwd**:
- single-repo → inside the repo (version-controlled with it, as today).
- multi-repo → in the umbrella folder at cwd (which may or may not itself be a git repo). It holds only the cross-repo planning artifacts (proposal / design / tasks / specs). It does **not** hold any sub-repo's code.

---

## Grounding (`config.yaml`) — per project, optional, never auto-generated downstream

`config.yaml` is always a **per-project, optional** artifact living inside a repo at `<repo>/feature-spec/config.yaml`. There is no multi-repo config.

- single-repo → read `feature-spec/config.yaml` if it exists; else scan the code.
- multi-repo → for **each repo the change touches**, read `<repo>/feature-spec/config.yaml` if it exists; else scan that repo's code. Never generate config for a repo here — only `/init`, run inside a repo, creates one.

What config uniquely adds over a code scan is the **vetted `hard_rules`** (confirmed by the user during `/init` SCAN). Without config, those are unavailable for that repo; everything else (stack, layers, entry points) is recoverable by scanning.

---

## Per-task repo binding (multi-repo only)

Every task targets file paths. The **owning repo** of a task is the child repo whose directory is a prefix of the task's paths.

- **A task group never spans repos.** Group tasks so each group lands entirely inside one repo — that keeps each group's commit atomic within its repo.
- A logical change that crosses repos splits into **one group per repo**, ordered by dependency: the repo that defines a shared contract (API, schema, shared type) goes first; consumers follow. This is the contract-first ordering `/propose` already uses, applied across repos.

---

## Git operations per mode

| Operation | single-repo | multi-repo |
|---|---|---|
| Worktree-base preflight (HEAD vs default branch) | once, on the cwd repo | per child repo a group targets, before dispatching that group |
| Phase 1 worktree isolation | worktree in the cwd repo | worktree created **inside the target child repo** (`git -C <repo> worktree ...`) |
| Per-group commit | in the cwd repo | in the group's target child repo |
| `/complete` artifact cleanup commit | commit the `feature-spec/` deletion in the cwd repo | code commits already landed per child repo during `/apply`; `/complete` deletes `feature-spec/` and commits that deletion only if cwd is itself a git repo — otherwise just `rm` (the umbrella is unversioned scratch) |

All other `/apply` mechanics (waves, merge-squash, Phase 2/3 reviewers, retry loop) are unchanged — they just operate within whichever repo the group is bound to.
