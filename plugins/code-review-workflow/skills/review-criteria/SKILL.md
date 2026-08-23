---
name: review-criteria
description: Load BEFORE reading a diff or reviewing code changes — before reviewing a PR, MR, commit, staged changes, or a patch, however small the ask. 看一下這個 PR, review 這個 diff, 幫我看這包改動, 這段有問題嗎, review this, check my changes, look over this patch. Criteria the running reviewer applies to its own reading; NOT a review tool, NOT a lint or style guide, NOT for auditing prompt or skill files.
user-invocable: false
---

# What is worth reading, and what is worth reporting

Most of a diff cannot be wrong in an interesting way. Reading it all costs the same as reading the
part that can, and the cost is paid out of the same budget — so a reviewer that reads everything
reviews the risky part worse, not better.

**Two gates, judged with the same care, failing differently.** Steps 1–4 decide reading depth, and a
wrong skip lands in step 4's counts as a file nobody opened — the reader can point at it. Step 5
hands over to gate B, which decides what gets written down, and a wrong suppression lands nowhere:
a review that saw the defect and dismissed it reads exactly like one where there was nothing. So
what differs is only which way to err where the criteria do not decide — steps 1–4 spend the
attention elsewhere, gate B writes it down. Nothing in steps 1–4 is ever a reason to stay quiet
about something you saw.

## Reading depths

| depth | what the reviewer does | what it does not do |
|---|---|---|
| `skip` | counts the file, reads nothing | does not expand the hunk |
| `diff` | reads the hunk as the diff shows it | does not open the file, chase callers, or read tests |
| `full` | opens the surrounding function or file, follows callers, reads the covering test | — |
| `metadata` | checks the name, the size, and whether the file replaces something | does not open it — where a binary's escalation lands, since there is no content to read |

Every changed file gets exactly one depth, and a file's depth is the highest any rule assigns it.
`metadata` sits outside that ranking — nothing assigns it by precedence; it is where the binary
row's exception in step 2 sends a file instead of to `full`. **It is also a ceiling for a binary,
whatever assigned it**: a project always-read list naming an image, or an escalation signal landing
on one, still gets `metadata`, because `full` on a file with no readable content is a depth nobody
can carry out.

**Precedence, highest first:**

1. The project's own never-read list — wins over everything below, including escalation
2. The project's own always-read list — `full`
3. Escalation signals (step 3) — `full`
4. Skip classes (step 2) — `skip`
5. Everything else — `diff`

## 1. Take the project's list before your own

Every repo has a place that is always worth opening and a place that never is, and no general rule
can know which. Look for an always-read / never-read declaration in the project's own agent
instruction file — `AGENTS.md`, `CLAUDE.md`, or whatever that project uses in their place.

Found → its paths take the precedence above, and they override these criteria rather than adding to
them. **What the project overrode is outside what this file claims**: a never-read path is skipped
on the project's authority, not on ours. It still counts, under its own label `project never-read`,
so that authority is visible rather than absorbed into the other numbers.

Not found → the rest of the steps run unchanged, and step 4's `project list` field reads
`none found`. **No repository to look in is a third state, not the same one** — it reads
`no repo access`, because "nobody declared a list" and "nobody could check" are different facts.

Records: the two path lists, or their absence. Step 4, the counts, reports which.

## 2. Assign the skip classes

Each class states the condition that makes the skip wrong. When that condition holds, the file is
`full` instead — the exception is the rule, not a caveat on it.

| class | label | skip because | wrong when |
|---|---|---|---|
| Machine-generated output — lockfiles, generated clients and stubs, compiled or minified bundles, test snapshots, vendored dependency trees | `generated` | the reviewable artifact is the input that produced it, and that input is elsewhere in the same diff | the generating input is **not** in this diff — someone hand-edited the output, and the edit is the change |
| Whitespace, import ordering, quote style, and other changes a formatter produces | `formatting` | the tool made them, and it makes the same ones every time | the diff mixes formatting with logic in the same hunk |
| Bulk rename, once a repo-wide grep for the old name comes back empty | `rename` | a rename nothing still refers to changed no behaviour | the grep hits anywhere, or any hunk is asymmetric |
| Pure deletions of a file already unreferenced in the diff's own scope | `deletion` | there is no new behaviour to be wrong | a reference to it survives, or the deletion is a migration someone has to follow |
| Binary and media assets — images, fonts, audio, video, archives | `binary` | there is no content a diff can show | it replaces an existing asset instead of adding one, or its size is out of line with its siblings |

A change that matches no class in this table is not skipped by this step — step 1's project list is
the only other thing that may skip one. Do not extend this table by resemblance during a run.

**The rename grep is the price of that row, and it is not optional.** A hand rename is exactly the
one that misses an occurrence, and the missed line sits in a file the diff never touched — so
checking the diff cannot find it. Grep every casing and separator form of the name (`aaa-bbb`,
`aaaBbb`, `AaaBbb`, `aaa_bbb`, the bare word), because a reference can cross forms where no compiler
follows it: a route, an i18n key, a CSS class, a DB column, a path inside a string. One search
against reading every touched file is still the cheap side.

**Two rows here need the repository, not just the diff** — this row's grep, and step 1's lookup of
the project list. Reviewing a pasted diff with nothing to search → the rename row does not apply,
those files stay at `diff`, and step 4's `project list` field reads `no repo access`, which is what
records that both rows were unreachable rather than merely unmatched. Never skip a rename on the
assumption that the grep would have come back empty.

**A binary escalates to its metadata, not to `full`** — the name, the size, and whether it replaces
something — because opening it reads nothing. A swapped asset is the case a file list shows and a
diff never does.

Records: the skip set with each file's class. Step 4, the counts, reports it.

## 3. Escalate on what can actually be wrong

Any of these makes the file `full`, whatever step 2 said:

- **A contract moved** — a function or method signature, a public type, an exported name, an API
  route, a payload field, an event name, a DB column. Follow the callers; the diff shows one side.
- **New control flow** — an added branch, early return, exception path, retry, timeout, or loop
  bound. A new path is a path nothing has exercised.
- **A value that is not just data** — a limit, timeout, retry count, feature flag, cache TTL, or
  permission constant. Changing the number is the whole change, so read what consumes it.
- **Money, authorization, personal data, or anything destructive** — payment and balance paths,
  authn/authz checks, PII handling, deletes, overwrites, and schema migrations.
- **Shared state or lifetime** — concurrency, async ordering, transaction scope, connection or
  handle disposal, caching. These fail somewhere other than where they are written.
- **A declared dependency version moved** — a pin in a manifest, an image tag. Read what this diff
  now uses from that package: a bump plus new symbols out of it is one change, not two, and the new
  version is where the behaviour came from. The **lockfile** stays skipped under step 2 — the
  manifest is the half that states intent, and escalating the resolved tree buys nothing.
- **A hunk that looks like the surrounding code but is not** — same shape as its neighbours with a
  different operator, boundary, or argument order.

Nothing here is a finding. Escalation buys the reading that decides whether there is one.

Records: the escalated set with the signal that escalated each. Step 4, the counts, reports it.

## 4. Count what you did not read

The `label` column is the vocabulary the breakdown is written in — a run that invents its own
cannot be compared with the one before it.

Four counts: read in full, skimmed, **metadata-checked** — where a binary's escalation lands,
checked but not by reading it — and skipped, broken down by the class each skip came from. Plus the
`project list` field, which is three-valued: `used`, `none found`, or `no repo access`.

**Every changed file lands in exactly one of the four, and the four sum to the number of changed files.** Count the changed files first and check the sum before writing the line: a file that appears in none of them vanishes from the accounting, and the line still reads as a complete one whatever it adds up to — nothing in the report shows the shortfall.

Without them, a review that skipped half the diff is indistinguishable from one that read it all.
They are what let the reader disagree with a skip, which is the only way a wrong skip ever gets
found.

Records: the four counts and the project-list state. Step 5's gate B holds the report layout they
are printed in, and adds its own counts beside them.

## 5. Read gate B before you write a single finding

Read `${CLAUDE_SKILL_DIR}/references/gate-b.md` now, with the reading done and nothing written yet.
It holds the three shapes a reported item may take and the one that is banned, the bar a finding
must clear, the four classes written nowhere and the condition that invalidates each, the ordering
rule, and the report skeleton every run fills in.

**This step is the last thing before the findings, not a reminder.** Reaching it after the
report is drafted means editing a list gate B would not have produced.

## What a skip is not

- **Not a verdict.** A skipped file is unread, never "reviewed and fine". Never report it as
  checked, and never let a summary's coverage claim include it.
- **Not binding once you have seen something.** Anything odd noticed while skimming a `diff` file is
  escalated on the spot and reviewed; the depth was a budget, not a permission. **The counts then
  record what you did, not what you planned**: a file you assigned `skip` and then read lands in the
  depth you actually read it at, and its skip class comes off with it. Left under `skipped` while you
  report on it, the tally contradicts itself and stops matching the changed-file total.
- **Not a reason to report less.** Depth governs reading only; what is worth reporting is step 5's
  gate B, and a file read at `diff` depth reports whatever it showed.
