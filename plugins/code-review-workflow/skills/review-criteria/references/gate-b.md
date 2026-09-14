# Gate B — what is worth reporting

**Every item is charged by what it costs the reader to settle, and that charge fixes its shape.**
Ten renames cost ten glances; one paragraph arguing toward a failure with no demonstrated trigger
costs the reasoning you did not finish. And a wrong suppression here shows up as nothing at all —
the defect was seen, dismissed, and the report reads like one where it never existed — which is why
nothing below suppresses on doubt.

## Three shapes, and one that is banned

| shape | what it is | format |
|---|---|---|
| **finding** | demonstrated: you can name the input or state that makes it break | `file:line` as the heading, the 1–5 line **verbatim quote** of the code it is about, then three labelled lines — **what breaks**, **trigger**, **fix**. Ordered by consequence, at the top of the report |
| **suggestion** | correct as it stands, and worth changing anyway — naming, inline this, a stray literal, a dead import, an asset out of proportion | the change **and its reason, always** — for an obvious one the reason is a word (`typo`), for the rest a clause saying what it buys. Never a chain of reasoning: if justifying it runs to a paragraph, it is not a suggestion |
| **unconfirmed** | a suspicion you could not demonstrate, **and only where confirming it would produce a finding** | one line, the claim plus **what would settle it**, so the reader is deciding whether to spend that, not whether to worry |

**Keep the last two apart** — a suggestion asks the reader to apply or drop it, an unconfirmed item
asks them to decide whether to go and check; interleaved, every line has to be re-weighed for how
sure it is. **Neither is a smaller finding**: a typo, a dead field and an oversized asset all run
correctly, and a suspicion has no trigger.

**The unconfirmed row has an entry test, and it is strict**: would the confirmed version clear the
bar? No — confirming it would only produce a suggestion — then drop it entirely rather than writing
it down unsure. That test is what stops this row becoming the bin every half-thought lands in, and
it leaves it holding only what a silence would actually cost. **A drop is still counted**, under
`below the bar` in the suppression breakdown: a test that removes items without leaving a number is
the exact failure the rest of this file is built against.

**The banned shape is the argument**: several sentences reasoning toward a failure, with no trigger
shown. It reads like a finding and costs like a research task, and it is the single most expensive
thing a review can contain. Either go and get the trigger, which makes it a finding, or compress it
to one unconfirmed line, if it passes that row's entry test. A suggestion's clause is not an
argument — it states what the code **is**, where an argument infers what it **might do**.

The compression is not a summary of the argument:
`utils/list.ts:11 — findLastIndex is ES2023 and the repo declares no browserslist. Settled by the
project's build target.` The claim, and the one step that ends it.

## The bar for a finding

Write a **finding** when at least one holds and you can show the trigger:

1. **It is wrong.** You can name an input or a state where the code returns the wrong result,
   throws, hangs, or corrupts something.
2. **It is a trap.** Correct today, and an ordinary future edit breaks it without any signal — an
   invariant nothing states, an ordering nothing enforces, a lifetime someone must remember to hold.
3. **It breaks a rule this project actually has.** A convention with a home in the repo — a
   documented standard, a linter rule, a pattern every sibling file follows. Not one you prefer.

**The quote is what makes the location survive.** A `file:line` on its own rots the moment anything above it moves, and it hands the reader nothing to match against — they take your word for where the thing is. The quote lets them, or any later pass over the same report, find the code again once the number stops pointing at it. Copy it exactly, only stripping a leading diff marker; for a finding about something *absent*, quote the nearest line the missing code should sit beside and say which side it goes on.

**The three labels are fixed, and that is the point**: a missing slot shows up as an empty label
instead of hiding inside a paragraph. Render them in the report's own language. **fix** carries the
direction in a clause, never a patch — without it the reader has a diagnosis and no ask, and
re-derives the change you already had in mind.

Clears the bar but has no demonstrated trigger → it is unconfirmed, not a shorter finding.
"consider…" is not a third option; that phrasing hands the reader the judgement you were asked to make.

## Suppress only what is worth nothing

Everything cheap and real becomes a suggestion. These four are written nowhere — each with the
condition that makes the suppression wrong, and when that condition holds it is reported. **A fifth
class, `below the bar`, counts alongside them** without being a row here: it comes from the
unconfirmed row's entry test above, which drops rather than classifies.

| class | label | suppress because | wrong when |
|---|---|---|---|
| A missing test where existing tests already exercise the changed path — e.g. a renamed local inside a function the suite already pins | `covered` | the coverage is there, just not new | the change adds a branch, boundary, or error path nothing exercises |
| A pre-existing problem this change did not introduce — e.g. a swallowed exception three lines above the edited hunk | `pre-existing` | a diff is not the place to renegotiate the file | the change makes it reachable, more frequent, or harder to fix later — or a whole-file review was what was asked for |
| A second instance of a root cause already reported — e.g. the same unvalidated id in four handlers | `duplicate` | one fix closes them, and separate entries read as separate problems | the instances need separate fixes; then it is one finding listing every site |
| Restating what the code does, praise, or a question you could answer by reading — e.g. "this adds a null check", "nice use of X", "is this called anywhere?" | `no content` | it spends the reader's attention and returns nothing | the remark had a consequence you had not written down — write the consequence and it is a finding or a suggestion |

The `label` column is the vocabulary the suppression breakdown is written in — with `below the bar`
from the entry test above, that is the whole legal set; a run that invents its own cannot be
compared with the one before it.

Every `e.g.` is one instance of its class, never the boundary of it. Do not extend this table by
resemblance during a run.

## Doubt is a line, never a silence

**Suppression is a positive claim that the item belongs to one of the four classes above**; anything
you cannot place there gets the unconfirmed line if it passes that row's entry test. What doubt costs
it is the shape, not its existence. **Nor does the count suppress**: there is no cap on any shape —
a cap drops a real defect the moment the count runs over; a long list is handled by the split above
and the ordering below.

## Order by what it costs to be wrong

Findings first, in this order: what breaks in production, then traps, then project-rule violations.
Within a tier, the one that is cheapest to fix goes first. Suggestions come next in file order,
then the unconfirmed lines — both are checklists, not rankings.

The reader works top-down and stops when they run out of time — a report whose first item is its
least consequential has failed this gate even when every item in it is real.

## The report

Two counting lines, then one section per shape. Fill this in; do not invent a layout per run.

```
Read in full: <n> · skimmed: <n> · metadata-checked: <n> · skipped: <n> (<class>: <n>, <class>: <n>) · project list: <used | none found | no repo access>
Findings: <n> · suggestions: <n> · unconfirmed: <n> · suppressed: <n> (<class>: <n>, <class>: <n>)

## Findings

**1. `<file>:<line>`**

```
<the 1–5 line verbatim quote>
```

- **what breaks**: …
- **trigger**: …
- **fix**: …

## Suggestions

- `<file>:<line>` — <the change>, <the reason>

## Unconfirmed

- `<file>:<line>` — <the claim>. <what would settle it>
```

The first line comes from gate A's step 4, the second from this gate. **A section whose count is
zero is left out** — the counting line already said so, and an empty heading reads as an oversight.
Headings and the three finding labels are rendered in the report's own language, settled in this
order: the language whoever asked for the review states outright — a dispatching workflow names one
in the prompt it hands you, and it names it there precisely because the prompt itself is not written
in it; failing that, the language the request came in; failing both, the language of the repo's own
comments. The counting lines
keep their keys as written, so a reader can compare two runs — and the suppression count stays even
when the section does not, because a suppression the reader cannot see is one they can never
disagree with.
