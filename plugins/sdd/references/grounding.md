# Grounding

Grounding — feeding the right facts into context before any code is written — is the single biggest driver of correct output in this workflow, more than any spec ceremony. `/propose`, `/apply`, and `/quick` run this as an explicit early step; a native coding session should do the same. sdd names no specific tool — use whatever the environment exposes — but you MUST reach for it deliberately, because lookup tools rarely auto-trigger.

The principle is **environment-agnostic by design**: sdd defines *what* to ground and *when*, never *which* tool. Skip any source that doesn't exist in the current environment.

## The three grounding sources (check in this order)

1. **Project knowledge** — before decomposing or implementing, check whether the environment offers a skill carrying project knowledge for the working repo(s), matched by repo name or path. If one exists, consult it first so decomposition, agent selection, and design reflect the repo's real responsibility, conventions, and cross-project dependencies. Quote its facts as written; do not infer from training data. (In multi-repo mode, do this per touched repo.)

2. **Curated project context** — `feature-spec/config.yaml` if present: its `architecture` block (pattern, layers, entry_points) grounds the codebase scan, and `hard_rules` are non-negotiable constraints. This is the only project context the workflow trusts — do NOT read the project's own prose docs (README, CLAUDE.md). If absent, the codebase scan is the grounding.

3. **External facts (front-load before designing/implementing)** — identify every fact the work will hinge on that is NOT obtainable from the repo or specs: a runtime/production config value (feature flags, rollout rates, limits), a cross-repo/service contract, live infrastructure state. For each one, **before you assume a value or let a plausible default stand, check whether an available tool can look it up** — a connected MCP server, a query/lookup tool, a project-knowledge skill — and **if such a tool exists you MUST use it rather than guess**. Resolve what you can NOW and feed the values into downstream context (the architect's prompt, the implementer's prompt, the design doc), recording how/when each was obtained.

## What you cannot ground → signal, never guess

Anything you genuinely cannot resolve with the tools at hand is an **external unknown**. Do NOT pick a plausible default. Use the `NEEDS` / `CONFLICT` / `BLOCKED` / `UNKNOWN` vocabulary defined in `skills/agent-guidelines/SKILL.md` → *Signaling Unknowns*:

- `NEEDS` — an external fact you can't obtain from repo + context. Stop that decision; the orchestrator resolves it (with the same tools above, or the user) and resumes you.
- `CONFLICT` — a spec/design disagreement.
- `BLOCKED` — a non-external blocker (insufficient context, task too large, unsound plan).
- `UNKNOWN` — an in-repo name/path you could not verify.

The whole point: grounding turns guesses into looked-up facts, and the signaling vocabulary turns un-lookable facts into an explicit pause instead of a silent fabrication. Together they are what keep the workflow from designing or coding on invented values.
