---
name: setup
description: "Interview the user and write knowledge.config.json for a new or existing company knowledge base. Runs before generate; does not generate files."
argument-hint: "[knowledge base repo path, or a config to revise]"
disable-model-invocation: true
---

# setup

Produces `knowledge.config.json` in the repository that will hold the knowledge base. Every other skill and the renderer read that file. Its fields and what each drives are in `${CLAUDE_PLUGIN_ROOT}/schema/config.reference.yaml`; the choices offered per question are in `${CLAUDE_PLUGIN_ROOT}/schema/presets.json`.

## The config file

- It lives at `<repo>/knowledge.config.json`.
- Only this skill writes it; the renderer reads it and never modifies it.
- A missing file is a first run. An existing file is a revision: its values are the proposal for every field, and the run changes only what the user asks to change.

## Steps

1. **Find the repository and the mode.** Take the argument as the repository path or the config path; with none, ask for the repository path, offering the current directory. Run `python3 --version`; the validator in step 5, validate a draft, needs Python 3, so without it stop and name that requirement. Records the repository path and the mode (first run or revision), which step 3, probe the repositories, and step 6, write the config, consume. Done when the directory exists and the mode is stated to the user. A missing directory is created only if the user agrees; if they decline, stop.
2. **Read the field list and the presets.** Read both files named above now; each holds what the later steps offer or fill. If either cannot be read, stop and say the plugin installation is incomplete.
3. **Probe the repositories before asking about them.** Ask for the folder that holds the source repositories (`paths.repos_root`) unless the existing config has it. Look at a bounded sample of repositories in that folder and say how many were looked at, then propose from what they show: git host, user label, the stack presets, and the environments. In a revision, probe only the fields the config leaves empty, or every field when the user asks to detect again. Propose connected tools only from the tools this session can see, and say when it cannot tell. Records a proposal table of field, value and the file or tool it came from, which step 4, confirm and complete the config, consumes. Done when every proposed value cites its source; a field with no evidence stays out of the table. An empty or missing folder is stated, and every field is then asked.
4. **Confirm and complete the config, one section per batch**, in this order: identity and paths (`paths.repo` is the repository path from step 1, not asked again); git; scope and ownership; environments; stack; capabilities; reader examples; known-context categories. Ask only where there is no proposal or two values fit; present a single proposed value for confirmation inside its batch. A question with a finite answer set offers the presets plus an other choice. A capability the user does not have is set to `none`, which removes its sections from the output. A team whose repositories and data the user can read is `reachable`; only a team they cannot read is a candidate for `(external: …)`. Take the audit and kit tuning fields from the reference defaults and list them in step 7, hand off, instead of asking. Records the config object, which step 5, validate a draft, validates. Done when every required field in the reference holds a value that is either confirmed or a stated default.
5. **Validate a draft.** Write the object to a scratch file and run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" --config <scratch file>`. Without `--write` the renderer only validates and prints a plan, so nothing is written. Fix every error answerable from what the run already knows; ask only when the answer is the user's knowledge. Done when it exits 0.
6. **Write the config.** When the file already exists, show the difference from the draft and wait for confirmation before replacing it; when it does not, write it. Done when the same command on `<repo>/knowledge.config.json` exits 0; cite its `plan:` line.
7. **Hand off.** Report the path written, the fields left at defaults, and the answers the user was unsure of, then name `/knowledge-generator:generate` as the next command. Nothing is rendered here. Done when the report contains all three.

Running this again on an unchanged config and accepting every proposal produces the same file.
