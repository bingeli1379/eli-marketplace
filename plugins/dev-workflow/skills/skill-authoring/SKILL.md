---
name: skill-authoring
description: Use BEFORE writing or editing any skill or agent prompt file — a SKILL.md, an agent .md, an output style, a bundled references/ or templates/ file — or any part of one: a description, a step, a guardrail, a flag. Covers trivial-looking edits and authoring done inside a larger task. Triggers on create, add, write, edit, refine, restructure, shorten, optimize a skill or agent, and their everyday forms: "make a skill for this", "tweak that skill", "clean this up", "add a rule to it", "why doesn't it trigger". Write-time side only — judging an existing file against criteria is the audit pass.
user-invocable: false
---

# Writing a skill

**Read `${CLAUDE_PLUGIN_ROOT}/references/authoring-rules.md` now, before you touch the file.** It is the catalogue of every rule about what a good skill or agent file looks like — trigger wording, examples, structure, naming, step handoffs, state changes, outside dependencies, safe editing, where content lives, and the order to cut cost in. Each entry states the rule, what breaks without it, and how the violation is visible. Follow it while writing; do not work from a memory of it.

The same catalogue is what `/review-skill` audits against, so the rules you write to are the rules you get checked against.

**A new rule goes in the catalogue, not in this file** — that keeps one home for it and gets it enforced on both sides at once. A rule about how to *converse* with the user belongs in neither: that is session conduct, and it lives in a `CLAUDE.md` or an output style.

## Before you call it done

1. Run the repo's own structure/lint script if it ships one — it catches name/directory mismatches, dangling reference paths, and glued step citations for free.
2. Run `/review-skill` on what you changed. It applies the audit form of the same catalogue; anything it finds was a rule that needed sharpening, so fix the file *and* consider whether the catalogue entry should have said it.
   **If it is not available**, do the two checks that catch the most on their own: re-read the full file top to bottom (not the diff), and for anything you inserted, ask the four insert questions from the catalogue's *Editing an existing skill* section.
