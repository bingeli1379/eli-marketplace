# Changelog

## [0.2.5] - 2026-08-23

### Added
- The authoring rules gain a fourth reason to pull material into a `references/` file: **when its effect depends on arriving late in the run.** Every run needs it, but read at load it is buried under everything read since — so the extraction buys position, not laziness. A rule that has to win against the model's default at the moment the output gets written is the shape. It carries a cost the other three do not, and the rules now say so: the pointer has to be obeyed, so it belongs in the step that uses the material, written as an action rather than a note.
- `/review-skill` gains two defect classes and a stronger closing sweep, aimed at the same problem: a run that finds one more thing every time you re-run it. **Class 13** catches an output slot whose legal values are defined nowhere — the report reads fine on its own and only fails when you put two runs side by side. **Class 14** catches a precedence order that resolves to an assignment the winning target cannot carry, which is invisible to every check that looks at one rule at a time. And step 7's blast-radius sweep now re-runs both against the text the fixes just wrote, because a fix is exactly what creates them — that is the defect shape that used to survive until the next round.

### Changed
- Two plugins you maintain can now lean on each other. The authoring rules used to ban every cross-plugin reference outright, so a plugin could only copy what its neighbour already owned. What actually breaks is the hard form — a file path into another plugin, or a step that cannot finish without it — while a skill loaded by name with a plan for its absence simply falls back to the plugin working alone. That lazy form is now the encouraged way to chain two of them, and a declared `dependencies` relationship still permits the hard form outright. `/review-skill` and `/improve-skill` were both rejecting the lazy form, so both move with the rule rather than after it.

## [0.2.4] - 2026-08-22

### Changed
- `/usage-audit` now opens with what your setup costs, not with how it measured. Three figures lead the report: what your skills charge every turn, how much of that never fires, and how much of *that* you would actually get back by removing something. The third one is new and it is the one that matters — the never-fired total includes silent skills sitting inside plugins you are keeping for another reason, which no uninstall reaches, so reading it as the saving overstated what a cleanup returns by more than half. The old Coverage block is gone: the session window moved under the MCP table it justifies, and anything the run could not read stays a line beside the cost figures.

### Fixed
- Every installed plugin now appears in the plugin table. It used to list only the ones that ship skills, so a plugin you reach entirely through its MCP server was missing from the inventory and got no verdict at all — on a real setup that quietly left out a server with 41 calls behind it.
- A plugin the run cannot measure is now left unjudged instead of being recommended for removal. One that ships only commands or agents, or whose install folder has gone missing, says which of the two it is. Treating "nothing recognised on disk" as "ships nothing" would have told you to remove three plugins that were working fine.
- The session window is read from the messages instead of from file timestamps. A transcript keeps being written to, so its file timestamp is when the session *ended* — the window looked like it began when the oldest session finished, hiding 24 of 55 days. A server with no calls over that window is the whole case for removing it, so a short window made that case look weaker than it was.
- The per-turn cost total no longer reads as your whole cost. The skills built into Claude Code charge their descriptions every turn as well and cannot be counted from disk, so the report now states which skills its totals cover and how many it had to leave out.

## [0.2.3] - 2026-08-22

### Changed
- `/usage-audit` now lays the report out as four tables instead of three. Every MCP server is listed and ranked by calls with the dead ones in bold, because a list of zeros cannot show a server *sliding* toward zero while it is still worth keeping. Your own `~/.claude/skills` are expanded one row per skill, since that is how you delete them; marketplace plugins stay rolled up per plugin, since that is how they arrive and leave. The plugin table now shows what a plugin weighs next to how much of that its silent skills are burning — one number without the other tells you nothing about whether to act.

### Fixed
- Skills and plugins that cost nothing are no longer billed as if they did. A command-only skill is not in the model's listing at all, and a disabled plugin loads nothing, yet both were being counted by description length — and both were topping the list of things to prune on a real run. They now read zero, and the disabled ones are named in Coverage so you can see they were excluded rather than missed.
- A server the report tells you to remove now tells you how. The removal command for each scope came back, including the one case where `claude mcp remove` cannot run at all — a project whose directory is gone — where the fix is a hand-edit of `~/.claude.json` and a backup first.
- Every plugin in the report now gets a verdict that fits it. A plugin whose every skill fires had no defined recommendation, and a row where all the silent skills were command-only could print a reason that was simply untrue.
- `/review-skill` now re-checks the commands and paths in a file that goes stale on its own. A `CLAUDE.md` naming a build command rots because the codebase moved, with nobody touching the file — so scoping that check to the diff passed a command that no longer runs.

### Added
- The authoring rules now settle what happens when another skill's guidance on writing skills is loaded on the same turn. This plugin's catalogue wins on judgment; the other source is trusted only for the harness mechanics it documents first-hand. Without that, whichever the model read last was the one that won.

## [0.2.2] - 2026-08-22

### Changed
- A slash command's argument now has a place to live that is not its description. Naming the three ways a skill can be reached told a command-only description to say what the command does and stop, which correctly pushed the argument out — and left nowhere for it to land, so trimming a description either dropped the argument or kept paying for it in the one field the person typing the command never sees. It goes in `argument-hint` now, which is what the slash-command menu actually shows you. The audit flags the two ways that field quietly does nothing: indented under another frontmatter key, or sitting on a skill you cannot type.

## [0.2.1] - 2026-08-22

### Fixed
- Editing a skill in a language other than English now pulls in the authoring rules. The write-time rules listed their everyday phrasings in English only, so a request phrased in your own language did not reach them and the edit got made without them — including the rule that "only trigger on the command" is a frontmatter flag and never something you write into the description.
- `/improve-skill` reads the authoring rules before it writes, not after. It used to reach them only through the audit it runs at the end, so its edits were measured against rules it had not yet read and the audit came back with findings against its own work.
- `/review-skill` no longer promises to finish a job it cannot. Pointed at something the size of a whole marketplace it kept going until it ran out of room and stopped partway with no record of what was left, which reads exactly like having covered everything. It now says up front how much it will not get to, works the files other files depend on first, and hands back the remaining list so a later run picks up from there.
- A server that made no calls is now sized instead of written off. The removal table used to call its context charge unmeasurable, which reads as zero; half of it is not, and that half is now counted per server — separating a real zero from a server that simply was not connected this session.

### Changed
- The authoring rules now name the three ways a skill can be reached, side by side, with what each one's description has to hold: selectable by the model, command-only, or model-only. The two failures they prevent are opposite — paying for a list of phrasings nothing can match, and trimming away the only surface that could have reached the skill at all.

## [0.2.0] - 2026-08-22

### Changed
- The plugin is renamed from `agent-ops` to `prompt-workflow`. The old install name no longer resolves, so reinstall as `prompt-workflow@eli-marketplace` to keep getting updates. The new name pairs it with `dev-workflow`: that one works on your code, this one on the prompt files that steer the model.
- `/usage-audit` only runs when you type it. A passing remark about your setup no longer reaches it, because the run reads your whole session history and starting that is your call.

### Added
- Writing, auditing, and improving prompt files now happen here. `skill-authoring` (the write-time rules), `/review-skill` (the audit), and `/improve-skill` (feed a real-usage problem back into a skill's source) moved in from `dev-workflow`, alongside the shared authoring catalogue they both read.
- The authoring rules now cover who may invoke a skill: decide it before writing the description and say it with the frontmatter flags, because a "never auto-trigger" sentence written into a description binds nothing and is charged on every request.

### Fixed
- The plugin now appears in the Codex marketplace. It had never been registered there, so Codex users could not install it at all while everything looked fine on the Claude side.

## [0.1.1] - 2026-08-21

### Added
- A project's MCP server whose folder is no longer on your machine is now called out as leftover config rather than skipped as unmeasurable — it can never load again, and the report names the `~/.claude.json` entry to delete. It says only that the folder is missing, never why: a check like this cannot tell a deleted project from one on a drive you have not plugged in.
- The list of skills that DID fire now shows what each one's description costs you per turn. A skill you called once that carries a long description is the one worth rewriting, and a table of call counts alone made it look no different from a cheap one.

### Fixed
- A project's MCP server the history never covered could be recommended for removal off the summary table alone, retiring something on evidence that was never collected. The summary now carries the same exception the detailed rules already had.
- Removing a project server whose folder is gone used to hand you a command that cannot run, because it has to change into that folder first. You now get the config entry to edit instead.
- Every zero-call server is shown with where it actually loads, which now includes "nowhere" for one whose folder is missing.

## [0.1.0] - 2026-08-21

### Added
- `/usage-audit` — tells you which of your installed MCP servers and skills have actually been used, and what to do about each: keep it, disable the server, or deal with a plugin whose skills never fire.
- Rows are ranked by what they cost you per turn, not by how many skills a plugin holds. A skill's description sits in context on every request while its body is only loaded when it fires, so a skill that never fires is a fixed charge for nothing — and thirty terse skills can cost less than six verbose ones. The report opens with that total and how much of it is going to waste.
- An unused skill is not treated like an unused server. A server nobody called is surplus. A plugin whose skills never fired is only dead weight if nothing else in it is reached either — another of its skills, or its own MCP server — and the run decides that from the data instead of asking you.
- Every server is reported with where it was declared and the command that removes it: your own config, a named project's config, or the plugin that ships it. A plugin-shipped server names both the plugin and its marketplace, because the same plugin name can exist in more than one.
- MCP results are per server, never per tool. Which tools a server offers can only be learned by connecting to it, so a tool that never fired cannot be told apart from one that does not exist — a server that never fired can be, and that is what you would switch off anyway.
- A fixed report shape — four sections, named columns, one row per item — so two runs can be put side by side.

### Notes
- Requires `python3`. Without it the run stops and says so; every verdict rests on the collection step, so there is no partial result worth showing you.
- Anything the run could not measure is named rather than counted as zero: a server whose project has no session history gets no verdict at all, and a name in your history with nothing installed behind it is left alone instead of being guessed into a rename.
