---
name: research
description: >
  Use when you need to understand an area of a codebase and produce a durable findings
  document to hand to someone else — how a flow works, what a subsystem touches, what
  depends on it, where the risks are — without proposing or making any change.
  Read-only: no spec artifacts, no code edits, no commits.
user-invocable: true
argument-hint: "<area — path, module, endpoint, or a flow like 'from X to Y'> [where to write it] [constraints]"
---

Read-only understanding pass over an area of the codebase, producing a **research findings document**. This is the read-only sibling of `/sdd:review`, one step earlier: `/review` judges code that exists (quality / security / performance / e2e verdicts); `/research` explains how an area works and what it touches, and makes **no judgement and no proposal**.

**When this earns its cost**: the understanding has to outlive the conversation — a handoff to another person, an onboarding note, input to a decision someone else will make. If the understanding is just for you, right now, plain conversational exploration is cheaper — say so and stop.

**Not this skill:**
- Want a change planned or built → `/propose` (durable spec) or `/quick` (small, fileless).
- Want code judged → `/sdd:review [target] [lens]` (omit the target for an architecture health scan).
- Debugging a specific failing behaviour → `systematic-debugging`.

---

**Input**: free-form prose describing the **area** — a path, glob, module/feature name, a flow (including one that spans services: *"from X to Y"*), or an endpoint. The same sentence may also state where to write the findings and any constraints (what to exclude, how deep, who will read it); Step 1 parses all of it out.

**Steps**

0. **Detect repo topology (MANDATORY first)**

   Load `${CLAUDE_PLUGIN_ROOT}/references/repo-topology.md` and run its Step 0 detection. Announce the mode. In **multi-repo** mode, resolve the area to the child repo(s) that contain it and scan each; the findings file lives at the umbrella cwd and labels every path with its owning repo.

1. **Parse the request, then resolve the area and output path**

   **The argument is free-form prose, not positional fields.** The user may write one sentence carrying the area, the output location, and extra constraints together (e.g. *"the registration flow from <service-a> to <service-b>, ignore the admin side, write it to the root of this folder"*). Extract from it: the **area**, the **output path** (if stated), and any **extra constraints** (things to exclude, a depth limit, an audience). Echo the parse back in one line — `Area: … · Output: … · Constraints: …` — so a misread costs one line instead of a whole scan. Never silently drop a constraint you were given.

   If no area is given, use **AskUserQuestion** (open-ended): *"What area do you want researched? (a path/glob, a module or feature name, a flow, or an endpoint)"*. Do NOT proceed without one.

   **PREFLIGHT — a cross-boundary area whose code you cannot reach (do this BEFORE scanning anything).** When the area names a flow that spans services, projects, or repos (*"from X to Y"*, an integration, a handoff between two systems), first check that each named side actually resolves to code in the working set (cwd repo, the umbrella's child repos, or an added directory). For every side that does not:
   - Say which side is missing and stop before the scan — do NOT start scanning the half you can see and discover the gap afterwards.
   - Ask the user to make it reachable (`/add-dir <path>`, or re-run from the folder containing both) **or** to confirm scoping the research down to the reachable side only, with the boundary treated as an external contract in the findings.

   Then resolve the area to a concrete scope:
   - **path / glob** → that subtree (if very large, say so and ask whether to narrow)
   - **module / feature / flow name** → `Glob` + `grep` to locate its entry points, then follow imports/callers outward
   - **endpoint / handler / SP name** → its definition plus every call site
   - **cross-service flow ("from X to Y")** → both sides plus the boundary between them: what X sends, what Y expects, and where the two definitions live. The boundary is the point of the research — trace it, don't summarize each side separately

   **Resolve the output path before scanning.** If the user gave one, use it. Otherwise propose one and get it confirmed — do NOT silently create a new top-level directory in someone's project. Propose, in this order of preference: an existing docs location the repo already uses (`docs/`, `notes/`, or wherever comparable notes live — check what exists), else `feature-spec/research/<area-slug>.md` (sdd already owns `feature-spec/`, and `/complete` never touches anything outside `changes/`). Confirm via **AskUserQuestion** with the proposal pre-selected.

   State the resolved scope and the confirmed output path in one line before scanning, so a wrong target costs seconds instead of a full scan.

2. **Read grounding context**

   Follow `${CLAUDE_PLUGIN_ROOT}/references/grounding.md` — consult any project-knowledge skill for the working repo(s) first, then `feature-spec/config.yaml` if it exists (its `architecture` block tells you where the layers and entry points are; `hard_rules` explain constraints you will see reflected in the code). `config.yaml` is optional — skip silently if absent.

   Do not read the project's own prose docs as authority. If a doc contradicts the code, **the code wins** — and that contradiction is itself a finding worth recording.

3. **Scan the area (thoroughness over speed)**

   Reuse the discipline of `propose`'s exhaustive scan, minus the change planning: `Glob` to enumerate, then open every file that could matter. Do not conclude from filenames. Reads may fan out to sub-agents that return compressed findings; nothing writes.

   Collect, with a `file:line` anchor for every claim:
   - **Entry points** — how execution reaches this area (route, command, event, signal, scheduled job, UI action)
   - **The flow** — the path through the layers, as a chain of named symbols (`A → B → C`), including where it branches
   - **Existing patterns** — how this area already does its recurring operations (data access, DI/wiring, error handling, logging, state, validation), naming the code that establishes each
   - **Dependencies** — inbound (who calls in) and outbound (what it calls: other modules, services, third parties, data stores)
   - **Boundary contracts** — every place a value crosses a boundary this area does not own (outbound request bodies/params, cookies, persisted shapes, URL/asset paths), and what the other side expects
   - **Test coverage reality** — which behaviours have tests and which do not, by reading the tests, not by assuming
   - **Risks / sharp edges** — what would break easily, what is duplicated, what is load-bearing but untested, what a newcomer would get wrong

4. **Ground every claim (no invention)**

   Same guard the architect works under: every path, symbol, and endpoint in the findings MUST come from what you actually read. Behaviour claims about a tool or framework MUST be verifiable by a concrete command or cite official docs.

   For a fact you cannot obtain from the repo — a runtime/production value, a contract owned by another service, live infrastructure state — check whether your available tools can resolve it (connected MCP servers, lookup tools, project-knowledge skills) and use them deliberately rather than assuming. Anything still unresolved is written into the findings under **Open questions** with what would answer it. Never fill a gap with a plausible guess; an unanswered question is a useful finding, a fabricated answer is a liability in a handoff doc.

5. **Write the findings document**

   **If the resolved path already exists, do NOT overwrite it silently** — someone else's findings doc is not yours to discard. Show its first lines and confirm via **AskUserQuestion**: overwrite / write alongside it (`<name>-<n>.md`) / cancel. Only then write.

   Write to the resolved output path (creating the directory if needed):

   ```markdown
   # Research: <area>

   > Scope: <what was scanned> · Repo(s): <name(s)> · Commit: <short SHA, or `n/a — no git` in no-git mode>
   > Read-only pass — no code, spec, or config was changed.

   ## Summary
   <5–10 lines: what this area is responsible for, and the two or three things
   someone must understand before touching it.>

   ## Entry points
   | Entry | Trigger | Lands in |

   ## How it works
   <The flow as named-symbol chains (A → B → C), with the branches. Anchor each
   step to `file:line`. Expand only the steps that are non-obvious.>

   ## Existing patterns
   | Operation | How this area does it | Established by |

   ## Dependencies
   **Inbound:** <who calls in>
   **Outbound:** <what it calls — modules, services, third parties, data stores>

   ## Boundary contracts
   | Boundary | Direction | Value / contract | What the other side expects |

   ## Test coverage
   <What is covered, what is not — read from the tests, with paths.>

   ## Risks / sharp edges
   - [category] <what is fragile> → <why it matters> (`file:line`)

   ## Open questions
   - <question> — <what would answer it (a command, a person, a system)>
   ```

   Keep it scannable: tables and chains over prose, one line per item unless a step genuinely needs tracing. A findings doc nobody can skim does not get read.

6. **Report and stop**

   Show the output path, a 3–5 line summary, and the count of risks and open questions. Then **stop** — do NOT offer to implement anything, and do NOT start a `/propose`. If the findings suggest work, say which command fits (`/propose` for a durable spec, `/quick` for small work, `/sdd:review` for a verdict) and let the user choose.

   Whether to commit the findings file is the user's call — mention it exists and is uncommitted. Do not commit it yourself.

---

## Guardrails

- **Read-only, no exceptions**: no code edits, no config edits, no `feature-spec/` artifacts, no `feature-spec/changes/<name>/` directory, no git writes of any kind (no commit, no stash, no branch, no `git restore`). The only file this skill writes is the findings document at the output path. Never run `propose`'s config-flip dry-run — it mutates the working tree.
- **No judgement, no proposal**: describe what is, not what should be. A verdict is `/sdd:review`'s job; a plan is `/propose`'s. Recording a risk is fine — prescribing the fix is not.
- **Every claim carries a `file:line` anchor.** An unanchored claim in a handoff doc is worse than an omission, because the reader cannot check it.
- **Unresolved facts go to Open questions** — never guessed into the narrative.
- **The code outranks the docs.** When they disagree, report the code's behaviour and record the discrepancy.
- **Say when the doc is not worth writing.** If the area is small or the understanding is disposable, tell the user that conversational exploration is cheaper and stop — a findings file with nothing durable in it is ceremony.
- Findings content in Traditional Chinese; code, paths, symbols, and technical terms in English.
