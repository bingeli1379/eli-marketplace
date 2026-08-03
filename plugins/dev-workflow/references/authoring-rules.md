# Authoring rules — the shared catalogue

**One home for every rule about what a good skill or agent file looks like.** Two skills read this file: `skill-authoring` follows it while writing, `review-skill` audits against it. A rule added here is enforced on both sides without touching either skill.

Each entry carries three things:

- **the rule**, in positive form — what good looks like
- **what breaks** when it is violated — the evidence that earns the rule its place
- **`→ check:`** how a reader sees the violation in the file, or **`→ process`** when it governs what the author does rather than what the file says (an audit skips those, and skipping them is not a gap)

Scope: the artifact and the craft of producing it — never how to converse with the user. How to answer, when to push back, what tone to take is session conduct and lives in a `CLAUDE.md` or an output style, not here.

## The description is the trigger, nothing else

- **Trigger conditions only** — the situations, symptoms, and phrasings that should reach this skill. A description that summarizes the workflow gets *followed* instead of the body. → check: the description holds conditions and phrasings, not a précis of the steps.
- **Enumerate the phrasings the user actually types** — colloquial as well as formal, and in every language they write in, since a description covering only the tidy English wording leaves the everyday ask to model judgement. Cover the *small* ask too ("just fix this one line" must reach the skill exactly like "audit this file" does). → check: everyday forms present, not only the formal verb list.
- **Describe the target by shape, never by naming example skills.** An illustrative `(/a, /b, /c, …)` narrows nothing, collides with each of those skills' own triggers, crosses plugin boundaries, and goes stale on the next rename. → check: no other skill or command named as illustration.
- **State what it is NOT when a neighbour is close** — "prompt files, NOT application code" is what stops the wrong skill winning. → check: a NOT clause exists whenever a sibling could plausibly match.
- **Keep it as short as the triggers allow.** Every skill's description sits in context permanently, while the body is lazy-loaded only when the skill fires — so the description is the one place where each word is a standing cost, paid on every request. → check: every sentence serves matching; no capability tour, rationale, or restated steps.
- **Never assert the user's setup as fact.** "You maintain several repos" is false for someone with one, and a false premise sends the agent hunting for something that does not exist. → check: claims about the user's environment are conditional.

## Rules first, examples second — an example becomes the whole permitted set

- **State the rule or shape; add an example only to disambiguate it.** An agent reading a list of examples treats that list as the boundary and does only those — the surrounding generality silently disappears. → check: each rule names the class, not just one instance of it.
- **The usual origin is a conversation.** The user names one case they just hit, and the rule gets written as that one case. Generalize it *before* it lands in the file: what class of thing was that an instance of? → process.
- **Where an example must stay, mark it non-exhaustive and make the rule the load-bearing half** — the rule sentence first, `e.g.` after, never a bare list standing in for the rule. → check: no bare list carrying a rule's weight.
- **The `description` is the exception, and only for phrasings.** Listing the words a user might say *widens* what reaches the skill — matching is not deciding, so extra phrasings add recall and cost nothing in judgement. Everywhere the skill decides what to *do*, the narrowing rule above holds. → check: phrasings enumerated in the description; the cases the skill handles enumerated nowhere.

## Write it structured

- **Use the form the content actually has.** A sequence → numbered steps. A set of independent items → a list. Several items sharing the same fields → a table, or a fixed bullet order, one entry per item. Prose is for the *why* that fits no slot. → check: sequences numbered, item sets listed, same-shaped items in a table or a fixed order.
- **Fixed fields make a gap visible.** When every item carries the same slots (what it is / when it fires / what to do), a missing slot shows up as an empty cell instead of hiding inside a paragraph. This is what stops one entry quietly lacking a rule its siblings have. → check: sibling entries carry the same slots.
- **A heading says what its section decides**, so the agent can reach the one it needs without reading the rest — and so you notice when two sections turn out to be the same section. → check: headings name decisions, and no two decide the same thing.

## Names and paths that resolve

- **Name a step, file, or section by what it does, never by its position.** `step1` / `step2` / `notes.md` carry zero information and go wrong the moment anything is reordered or inserted. `2. Validate the config file` survives a reorder; `step 2` does not. → check: no position-shaped or contentless names.
- **Cite a step by number AND name** — `step 2, the text pass`. A bare `step 4` points at whatever lands there after the next renumber. The number is a coordinate; the name is its identity, and only the name survives a reorder. → check: every step citation carries the name.
- `name:` MUST equal the parent directory exactly, lowercase and hyphens. A mismatch is a silent load failure — the skill simply never appears. → check: compare the two strings.
- A bundled-file read needs a base: `${CLAUDE_PLUGIN_ROOT}/…` for plugin-level files, `${CLAUDE_SKILL_DIR}/…` for the skill's own. A bare `references/x.md` resolves against the **user's** working directory and reads nothing. → check: no read instruction with a bare relative path.

## Steps: name what each one hands the next

- For every step, write down **what it records and who consumes it**. That sentence — "record the range; step 2 reuses it" — is the only thing that makes the break visible when someone later edits either side. → check: each step names its output and that output's consumer.
- **Done-conditions must be checkable**, and exhaustive where it matters ("every changed file accounted for" bites; "produce a list" does not). An unfalsifiable bound lets the agent declare victory early, and it slips hardest when the later steps are already in view. → check: each step's bound is falsifiable.
- **Give a positive target alongside a prohibition**, keeping the ban's force. A bare ban leaves the forbidden behavior as the last pattern the agent read. → check: bans are paired with what to do instead.
- **Every branch needs a landing place**, and a jump must survive its own step being skipped — a "go to step 6" living inside step 2 never fires when a flag skips step 2. → check: every named branch or jump has a defined target reachable on all paths.
- **A step that could ask the user must state on the page which it does — decide, or ask.** Write "ask" only where two readings lead to materially different work, and have the step offer options when it does; anything determinable from what the run already has, the step determines. Left unstated, every such step becomes a question and one task turns into a questionnaire. → check: such steps say which.
- **A step that claims completion names what proves it** — the command it ran, the output it read, the file it re-read. "Done" with nothing behind it is an assertion. → check: completion steps cite concrete evidence.
- **A flag or mode is a branch, not a discount.** Adding one is legitimate when two inputs genuinely need different work — name the condition that selects each branch, and make the run say which branch it took so the user can see the path rather than guess it. What is not legitimate is selling a branch as cheaper coverage: if the only difference is "does less of the same work", that is a saving to find in the flow, not a switch to hand the user. Where a branch does cover less, its output states what it skipped. → check: each flag names its selecting condition; no flag whose only effect is reduced coverage.

## If the skill changes state

Only applies when it writes files, runs git, dispatches work, or produces artifacts — a pure reference skill has no state, and skipping this section for one is correct, not a gap.

- **Say what a second run does.** Re-running after a crash, a retry, or the user simply running it twice must not double-apply work, skip work, or mistake its own earlier output for fresh input. "It depends" means nobody checked. → check: the file answers the question explicitly.
- **Guard anything destructive.** For delete, overwrite, purge, reset: state the guard — a dry run, a confirmation, a scoped path — *before* the action, not after it. And never let "half done" or "never started" be classified as "done" and then discarded; that is how work disappears silently. → check: a guard precedes each destructive action.

## Depending on anything outside the file

- **Keep the skill able to stand alone.** Never read a path belonging to another plugin, and refer to a sibling skill by name only, never by path — a skill that reaches into its neighbour breaks the moment that neighbour is not installed. → check: no cross-plugin path; no path into a sibling skill's directory.
- **Every outside dependency needs an absence plan**: a missing argument, a tool or MCP server that is not wired, a sibling skill that cannot be reached, a file or artifact that is not there. For each, write two things — how the absence is detected, and what happens then (proceed with less, or stop and name what is missing). Put it where the dependency is first used, so it is checked up front instead of discovered mid-flow. → check: each dependency has detection plus consequence, stated at first use.
- **Absence is announced, never silent.** A skill quietly doing less looks exactly like a skill that found nothing. → check: the reduced path's output states what was skipped.

## Editing an existing skill

- **Read the steps either side of your edit before making it.** Almost every broken chain comes from editing one step's text while its neighbours still describe the old handoff — the edited sentence reads perfectly, and the seam is what broke. → process.
- **Know whether the edit preserves behavior, and make the file show it either way.** A restructure is behavior-preserving: same decisions, same outputs, only wording or layout moves — so check the outputs are actually unchanged before treating it as one, because an "optimization" that quietly decides something differently is the worst outcome here and the diff will not flag it. When behavior does change, the change has to land on every surface that documents that behavior — the README, the manifest, the changelog. **Merging or removing a skill, a command, or a flag is always that case**, never a silent cleanup. → check: an interface change appears on the documenting surfaces, not only in the diff.
- **Before changing a rule, grep a distinctive token from it.** A rule usually lives in 3–6 places: its canonical section, a summary table row, a checklist line, a guardrail, the README, manifest keywords. Fixing one and missing the rest is the most common defect there is, and one grep is the whole cure. The same applies to **renaming a term** — every occurrence moves together or the file now says two things. → check: no copy of the changed rule still states the old version.
- **One concept, one term, whole file.** Drifting between synonyms (pass / round / phase; target / file / subject) reads as three different things and the agent treats them as such. Pick the word, then grep the synonyms out. → check: one concept never appears under two words.
- **When you INSERT into a step**, check exactly four things about that step: its declared limits, what it records, who reads what it records, and which gate must precede its actions. Every inserted sentence reads correct on its own — the break is always in the neighbour. → process.
- **When you REMOVE a flag, mode, or step, sweep its skeleton**: its report template, jump instructions, `(x only)` qualifiers, and the sentence that existed only to contrast it. Leftovers imply a mode that no longer exists. → check: nothing left refers to the removed thing.
- **Never delete a rule to tidy up.** Assume it is there because something failed without it; count list items before and after an edit. → check: item counts reconcile across the change.
- **Do not invent a capability for another role.** If a step says "the agent reports X", that agent's own contract must gain the duty, or nothing reports X and the check silently never runs. → check: every duty asserted for a role exists in that role's own instructions.

## Where content lives

- **Steps in `SKILL.md`; rule catalogues and criteria in `references/`.** Push too little down and the steps drown; push too much and the agent never reaches it. → check: the steps are legible on their own.
- **Extract when it buys one of three things**: the material is read only on *some* runs so extraction makes it lazy; it is shared by two or more steps or skills, so one file becomes the single home instead of two copies drifting; or it is a bulky catalogue that would bury the steps. Sharing works within a plugin — across plugins each stays self-contained, and there the duplication is deliberate. → check: each extracted file satisfies one of the three.
- **Do NOT extract what has one reader and always loads.** It costs the same tokens plus a hop, and the indirection is a new thing to get wrong. → check: no single-reader always-loaded reference.
- **Pointer wording is the reliability lever** — imperative, naming what is behind it and when to read it ("Read X now; it holds A and B"). A vague "see the reference" fires on some runs and not others. → check: every pointer names its content and its trigger.
- **A reference is part of the unit, not an appendix.** After extracting, check that whatever selects files — a scope filter, tooling, the audit — still sees the new location, and remember an edit inside it implicates the steps that drive it. → check: file selectors cover the reference locations.
- **A skill that emits a document ships the document as a template file** (`templates/…`) instead of describing its format in prose. The template is copyable, has one home, and keeps the steps short — they then only say when to use it and what to fill in. If the output's language matters, fix it in one place rather than restating it per step. → check: document formats live in template files, not in step prose.
- **One canonical home per rule.** A guardrail restating a step's rule is house style; a second full copy of a block is drift waiting to happen. → check: no substantial block exists twice.

## Cost: make it smaller in this order

Bloat is real and so is over-trimming, so the order matters — cheapest, safest saving first.

1. **Change the flow so the words are not needed.** The real wins are structural: a check that makes a whole branch unnecessary, a grep replacing a read-everything sweep, one read serving two layers, a result computed once and reused instead of re-derived per item. This is where the large savings live, and coverage does not move. → process.
2. **Merge near-duplicate wording inside the file.** Three bullets circling one idea, a qualifier repeated on every step, two steps sharing a paragraph of boilerplate — collapse them into one statement in one place. The agent then reads one clear rule instead of three overlapping ones, which also removes the "which of these applies?" hesitation. **The test before merging is whether they fire together**: same situation, same demanded action → merge. Different trigger conditions, different actions, or two distinct vocabularies (two rating scales, two fix policies) → keep both, however similar the words look. Merging those hides one of them, which costs correctness rather than tokens. → check: no two entries demand the same action in the same situation.
3. **Extract rather than delete** when the material is real but not always needed — see *Where content lives* for when extraction actually pays. → process.
4. **Then cut the lecture, never the rule.** Delete what teaches a concept the model already has, and delete duplicated prose. **Rationale splits in two**: a "why" that records a real failure ("a bare path resolves against the user's cwd") is evidence and stays — it is what stops the rule being re-litigated; a "why" that explains a general principle goes. A one-line rule is not bloat even when the concept is obvious. → check: no tutorial prose; every rule still present.
5. **Never buy brevity by shortening a rule into ambiguity.** A rule squeezed until it could be read two ways costs more than the tokens it saved, and the loss is invisible until something behaves wrong. → check: no rule readable two ways.
