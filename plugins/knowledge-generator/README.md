# knowledge-generator

Generate a project-knowledge skill and its maintainer toolkit for any company. You answer a few setup questions about your repos and tooling; a script renders the templates, and an AI fills in the knowledge from your code.

The generator supplies structure and rules. The knowledge itself comes from you and your repositories, never from the AI's imagination.

## Status

Early version. The renderer, the config schema and every template are tested. The two skills, `setup` (an interview that writes the config) and `generate` (renders it), are written and checked statically, and both have run once in a live session against a real set of repositories.

## Install

```
/plugin marketplace add bingeli1379/eli-marketplace
/plugin install knowledge-generator@eli-marketplace
```

## Use

Needs Claude Code and Python 3 (standard library only).

1. `/knowledge-generator:setup` interviews you and writes `knowledge.config.json` into the repository that will hold the knowledge base.
2. `/knowledge-generator:generate` validates the config, shows what would be overwritten, renders the tree, checks that the committed kit is not git-ignored, and tells you what to fill in next.
3. Paste `CLAUDE.snippet.md` into your own CLAUDE.md, then document your first project with `/<prefix>-knowledge-add-project`. The maintainer kit is already in your repository's `.claude/skills/`, committed with it, so every clone has the commands.

You can also write the config by hand and run the renderer yourself (see "Rendering by hand").

## What you get

For a config with prefix `acme`, rendered into a repository:

```
README.md                                   your knowledge base's README (yours to edit)
CLAUDE.snippet.md                           routing lines to paste into your own CLAUDE.md
skills/acme-knowledge/                      the reader skill, loaded lazily from its description
  SKILL.md
  references/project/index.md               yours to fill in
  references/domain/index.md                yours to fill in
  references/observability.md               only when you configured logs, dashboards or one schema repository per database; yours to fill in
  references/platform-basics.md             only when a shared catalog is set in the config by hand; yours to fill in
.claude/skills/                             the maintainer kit, committed with the repository
  README.md
  acme-knowledge-authoring-core.md          shared rules, the single source every skill points to
  acme-knowledge-local-rules.md             rules specific to your company, yours to edit
  acme-knowledge-add-project/               add or update a per-project doc
  acme-knowledge-add-domain/                add or update a domain doc
  acme-knowledge-sync-local/                audit the whole base against your clones
  acme-knowledge-verify/                    review someone else's changeset
  acme-knowledge-list-markers/              list every open marker
```

The reader skill is the only one the model may pick on its own, so its description is composed from your config: your teams, example projects and flows, and the tools you configured. Every kit skill is command-only, so it runs only when you type its command.

## How it works

1. A config file describes your company: the repo layout, owners, environments, the stack you use (read from your repositories; only where your services run is asked, and only when they show none), and which verification capabilities you have (logs, dashboards, a settings store, a schema source, an external reference such as a wiki).
2. The renderer turns that config and the templates into the tree above. A capability you do not have removes its sections, anchors and probes entirely instead of leaving empty headings.
3. Files you are meant to edit (`README.md`, the two `index.md` files, `observability.md`, `platform-basics.md`, the local rules) are written once and never overwritten, so regenerating after a generator upgrade refreshes everything else and leaves your content alone. The one exception inside a generated file is the Platform basics list in the reader `SKILL.md`: write your facts between its `<!-- keep -->` and `<!-- /keep -->` lines and every render carries them over. The list starts from the categories you chose in the config; adding or dropping a category later is a hand edit there.

The shared rules are about trust: every fact is verified against code or visibly marked, every fact carries an anchor that makes staleness cheap to catch, and a periodic audit keeps the base correct over time. The rules and the audit mechanism ship with the kit; you do not have to design them.

## Config

The shape of the config is documented in `schema/config.reference.yaml`; the file itself is JSON, because the renderer uses only the Python standard library. Three complete examples live in `tests/fixtures/`: `acme` has every capability on, `fakeco` has most of them off, and `minimal` has them all off.

## Rendering by hand

Python 3 is the only requirement, with no packages to install. The commands below assume a clone of this marketplace; an installed plugin keeps the same `scripts/render.py` under its own plugin directory.

```bash
python3 plugins/knowledge-generator/scripts/render.py --config my.config.json           # validate and list what would happen
python3 plugins/knowledge-generator/scripts/render.py --config my.config.json --write   # apply
```

A hand render does not touch `.gitignore`; run `git check-ignore -v .claude/skills/README.md` yourself so the kit stays committed.

The output goes to the repository and subdirectory the config names (`paths.repo`, `paths.out`). Without `--write` nothing is written: you get a one-line count, the user-owned files that would be kept, and a diff for every generated file that differs from what a render writes.

The renderer is strict. An unknown name in a template, an unbalanced block, or a config that fails validation stops the run with a message that names the problem; nothing is written as an empty string.

## Development

```bash
python3 -m unittest discover -s plugins/knowledge-generator/tests
```

Templates use `{{ name }}`, `{{#if x}}` / `{{else}}`, `{{#unless x}}` and `{{#each list}}`. A block tag alone on its line removes the whole line. Every condition is computed once in the renderer's `derive()` step, never inside a template. A template that renders to nothing but whitespace is not written; that is how a whole file is switched off.

## License

MIT
