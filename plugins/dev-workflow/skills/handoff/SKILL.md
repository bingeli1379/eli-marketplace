---
name: handoff
description: Compact this session into a file another agent, another window, or another harness can pick the work up from. NOT /compact or /clear (same thread, same window). NOT a PR description, and NOT standing project facts, which belong in CLAUDE.md.
argument-hint: "下一個 session 要接著做什麼？"
disable-model-invocation: true
allowed-tools: Bash(git log:*), Bash(git status:*), Bash(git rev-parse:*), Bash(git diff:*), Bash(ls:*), Bash(cat:*), Write, Read
---

# Handoff

**Goal**: a file that lets a session holding none of this conversation continue the work without asking the user a question the session already answered.

Its reader is an agent with zero context. Everything it needs to act is either in the file or named by a path it can open.

## Where it goes

`HANDOFF.md` at the top of the working directory, beside the README. It sits where the user will see it without remembering a path, and where one `rm` removes it when the work lands.

- **A `HANDOFF.md` already exists → read it and show the user what it holds before writing.** It is a previous handoff, possibly the one that started this session; replacing it unasked destroys the only copy. Confirm, or write `HANDOFF-<slug>.md` beside it, `<slug>` named for the work.
- The working directory is a repo and `HANDOFF.md` is not ignored → say so in one line and offer to add it to `.gitignore`. A handoff at the repo root is one `git add .` away from being committed, and it holds whatever this session was in the middle of.
- No git here → nothing to ignore, and the file still goes to the same place.

## What goes in it

Fixed sections, in this order, their headings as written here. The body is in the language this session is being held in, leaving paths, identifiers and command output verbatim. A section with nothing in it is written `無` rather than dropped, so the reader can tell an empty answer from a missing one.

- `## 在做什麼` — the goal and why it matters, 2–4 sentences. What breaks if nobody finishes it. Not a chronology of the session.
- `## 已完成` — one line each, with its evidence: a commit SHA (`git log --oneline` for the range this session produced), or a file path. **Paths are absolute, or repo-relative with the repo named** — a bare relative path resolves against whatever the next session's cwd happens to be. No git in the working directory → say so and cite paths only.
- `## 還沒做` — work the next session can pick up and do, one line each.
- `## 等你決定` — what is open because only the user can settle it, one line each, each naming the options. Kept apart from `還沒做` because the next session acts on everything in that section: a decision filed there is taken as a task and decided by whoever reads it first.
- `## 已決定不做` — every path considered and closed, each with its reason and what would have to change to reopen it. **The section that decides whether the file works.** A closed decision left out of it reads as an open task, and the next session spends its run re-deriving a conclusion this one already reached. Measured: a handoff that listed one such decision under 還沒做 sent a fresh agent into it for its entire run, and the same document with the decision moved here was picked up with no questions at all.
- `## 沒驗證的假設` — anything this session believed but never checked. The next session treats the rest of the file as fact, so an unmarked guess becomes a premise it builds on.
- `## 查過的來源` — specs, issues, MRs, docs, dashboards, long files already read: path or URL plus the one line taken from it. Reference them; do not copy them in. A session that read a lot is exactly the one whose handoff must not restate it.
- `## 建議載入的 skill` — which skills the next session should load, by name.

If the user passed an argument, it says what the next session is for; weight the sections toward it and keep the rest short.

## Flow

1. **Collect the evidence before writing.** `git log --oneline` for this session's commits, `git status` for what is uncommitted, and the paths of everything this session read or produced. Anything not in this collection does not go in the file as fact.
2. **Settle the destination first, then write the file** — run the existing-`HANDOFF.md` check from *Where it goes* and wait for the user's answer before any write, since that is the step that can destroy a previous handoff. Redact credentials, tokens, and personal data — a handoff travels further than the session did.
3. **Read it back as the next session would**, holding nothing but the file: for each item under `還沒做`, ask what you would have to go back and ask the user. **Every such question is a gap — fill it from this session and re-read, up to 3 rounds.** What remains after that is a genuine user decision, and it goes under `等你決定` with its options.
4. **Report the path and what step 3 left for the user.** Nothing else.

## Guardrails

- The file states what this session established. A gap stays a gap — writing a plausible answer into it is the one failure the next session cannot detect.
- No chronology. What was tried and abandoned belongs under `已決定不做` with its reason; the order things happened in carries nothing.
- Repo-wide facts that hold beyond this task — conventions, build commands, architecture — belong in `CLAUDE.md`, not here. This file holds only the unfinished work.
