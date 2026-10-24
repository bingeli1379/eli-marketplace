---
name: generate
description: "Render the knowledge base tree from knowledge.config.json into the configured repository. Needs the config that setup writes."
argument-hint: "[path to knowledge.config.json]"
disable-model-invocation: true
---

# generate

Turns `knowledge.config.json` into the tree listed under "What you get" in `${CLAUDE_PLUGIN_ROOT}/README.md`. The files fall into two classes. Generator-owned files are rewritten on every run. User-owned files (`README.md`, the two `index.md` files, `observability.md`, `platform-basics.md`, the local rules) are written once and never overwritten, so the user's content in them survives every later run. One generated file also holds user content: the reader `SKILL.md` carries its Platform basics between `<!-- keep -->` and `<!-- /keep -->` lines, and a render keeps whatever is between them.

The renderer is `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" --config <config>`. Run as is, it validates the config and writes nothing: it prints a one-line count of `new`, `changed`, `unchanged` and `kept` files, lists the user-owned files it would keep, and shows a diff for each generated file that differs from what a render writes. Adding `--write` applies the render into `<paths.repo>/<paths.out>`.

## Steps

1. **Locate the config.** Take the argument, else `knowledge.config.json` in the current directory. If it is absent, stop and name `/knowledge-generator:setup`. Run `python3 --version`; without Python 3 stop and name that requirement. Records the config path, which every later step passes to the renderer. Done when the file is found and Python 3 answers.
2. **Plan, and guard the files that would be overwritten.** Run the renderer without `--write`. A non-zero exit is a config error: stop, show it, and name `/knowledge-generator:setup` as the place to correct the answers. A `changed` file is a generator-owned file that differs from what a render writes: either someone edited it by hand, or the generator was updated since the last run. Show the user each such diff and wait for confirmation before step 3, render. Company-specific rules belong in the local rules file, which is never overwritten; say so when the user's edits look like rules. Records the counts and the `changed` files, which step 3, render, acts on. Done when no file is `changed`, or the user confirmed each one listed; if the user declines, stop with nothing written.
3. **Render.** Run the renderer with `--write`. Validation and rendering finish before the first file is written, so a non-zero exit means nothing was written: report the error and stop. Done when it exits 0; cite its `done:` line.
4. **Keep the link directory out of version control.** In `<paths.repo>`, run `git check-ignore -q <kit.link_dir>/probe`; the path must sit inside the directory, because a directory-only ignore rule does not match a directory that does not exist yet. When it reports not ignored, append `<kit.link_dir>/` to `.gitignore` and say so. Without git, or outside a repository, skip this and say it was skipped. Done when the directory is ignored or the skip is stated.
5. **Report the next actions.** List the user-owned files that step 3, render, printed as `wrote`: those are new and meant to be filled in; a `kept` one already holds the user's content. Point to the activation commands in `<paths.repo>/<paths.out>/local-tools/README.md` under "Activate" and do not run them. Name `CLAUDE.snippet.md` as the block to paste into the user's own CLAUDE.md, which this skill does not edit. Name the first authoring command, `/<prefix>-knowledge-add-project`, available once the kit is activated. Done when the report holds all four and cites the step 3, render, `done:` line.

A second run on an unchanged config leaves every file with the content it already had and every user-owned file untouched.
