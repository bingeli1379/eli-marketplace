# Sweep catalogue

Two open sets: where drag hides, which the slice audit hunts, and what a trim breaks, which the review after it hunts. Each entry says what to look for; the instance after it is the observed case, not the boundary.

## Where drag hides

- **Bundled references a previous trim never reached.** Trim passes edit `SKILL.md` bodies and leave their references alone, so a reference whose last commit is the repo's first is the first place to look. Observed (2026-10): about 4,600 of 5,100 removable lines sat in references untouched since the repo's first commit, a month after their `SKILL.md` files had been trimmed.
- **Textbook material** — primers on what the model already knows (query plans, normal forms, mocking anti-patterns), with no recorded failure behind them. They drift from the skill that points at them: observed, a reference demonstrating a global setting raise its own skill called a last resort.
- **A rule restated across files** — written in full in a skill and again in its reference, an agent, or a workflow step. One copy stays; the others become pointers.
- **Guardrails restating their own file's steps.**
- **Dead modes** — a mode, branch, or template no caller reaches. Observed: an orchestrator's free-form mode with zero direct spawns in transcripts, still carrying a report template that competed with the adopting skill's.
- **Workarounds for behaviour now native** — an instruction the harness or a tool now enforces itself (a "do not poll or sleep" the harness now blocks; a parameter the tool schema now marks required). A recipe calling a tool in a way it never supported belongs here too: observed, a Grafana templating function sent as a PromQL query.
- **Emphasis volume** — caps, "NOT optional", a third restatement, around a rule nobody recorded being skipped.

## What a trim breaks

Every class below was introduced by a trim and caught only by a review afterwards (observed, 2026-10).

- **A condition deleted with its sentence.** The removed bullet carried a condition the surviving rule did not: a "categorize a commit without a Conventional Commits prefix by its diff" line was what kept a mechanical bump rule from calling an unprefixed feature a patch.
- **A shorter form that covers less.** A credential rule shortened from "anything pasted to chat" to "chain notes and dumps", while the rule still covering chat loaded only at a later step; a ban merged into a neighbour that named only three of the cases.
- **The surviving copy loads for some readers only.** Deleting a duplicate leaves every reader that never loads the other home without the rule: a no-refactor rule cut from a checklist every agent loads survived only in a TDD skill some agents never load. Check who eagerly loads the home that stays.
- **A pointer that widens or narrows its target.** "Pause only for what X admits", where X admits a case the replaced text excluded.
- **Numbers cited elsewhere.** A section, step or criterion number that other files or scripts cite, whose guard note against renumbering was itself pruned. Grep the number's form across prompts and scripts, not only prompts.
- **A script reading the prose's vocabulary.** A bundled script matching labels or headings the edited prompt no longer emits.
- **A tool recipe rewritten from memory.** Check the tool's real parameter shape: separate `matches` entries are OR'd, so splitting two filters made every label probe look like a hit.
- **Two competing templates.** Removing a mode leaves its report template alongside the caller's.
