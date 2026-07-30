# Design It Twice

Your first idea for an interface is rarely your best one. One designer working alone in one context does not really compete alternatives — it elaborates its first shape and calls the elaboration a comparison. This is the fan-out that fixes that: generate rival interfaces **in parallel, in separate contexts**, then judge them against each other.

Uses the [SKILL.md](SKILL.md) vocabulary — **module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**.

## When it applies

Only when the change **defines a new interface others will depend on**: a new API contract, a new shared type or module boundary, a new seam between layers or repos.

Skip it when the shape is already determined — the change mirrors an existing Reference implementation, it is precedented CRUD, it is a refactor whose target shape is fixed, or it only touches interfaces that already exist. There is nothing to compete, so three proposals cost tokens and return one answer you already had.

## 1. Frame the problem space

Before dispatching anything, write down what any candidate has to satisfy:

- The constraints the interface must meet (spec acceptance criteria, `hard_rules`, existing conventions it sits beside).
- Its dependencies, and which category each falls into (in-process / local-substitutable / remote-but-owned / true-external) — this is what decides how the module gets tested across its seam.
- A rough code sketch to make the constraints concrete. This is **not** a proposal, only a way to stop the constraints from being read three different ways.

Show this to the user, then start the fan-out immediately — they read while the designers work.

## 2. Fan out

Dispatch **3 designers in parallel in one message** (Agent tool, `run_in_background: true`, distinct `name`s like `design:minimal`).

**Do NOT grant these three `mode: "bypassPermissions"`.** They return text and write nothing, so they never hit a permission prompt to bypass — and withholding it means a designer that tries to write anyway is stopped by the prompt instead of silently landing a file while its two siblings write the same one. Reserve that mode for the single agent that actually writes the artifact afterwards. Say it in each prompt too: **"Return your proposal as text. Do NOT create or edit any file."**

Every designer gets the **same** technical brief — affected-files inventory, specs, relevant `config.yaml`, the framing above — and **one different constraint**:

- **minimal** — "Minimize the interface: 1–3 entry points, maximum leverage per entry point."
- **flexible** — "Maximize flexibility: support the extensions and use cases this domain plausibly grows into."
- **common-case** — "Optimize for the most common caller: make the default path trivial, even at the cost of the rare one."
- **ports-and-adapters** *(add only when the dependency crosses a network or third-party boundary)* — "Put a port at the seam; production and test each get their own adapter."

The constraints must be **genuinely opposed**. Three designers all told "design a good interface" return the same interface three times, which is the failure this whole step exists to avoid.

Each returns **as text — no file writes**:

1. The interface — types, methods, params, **plus invariants, ordering constraints, and error modes** (interface here means everything a caller must know, not just the type signature).
2. A usage example showing how a caller actually uses it.
3. What stays hidden behind the seam.
4. Dependency strategy and adapters.
5. Trade-offs — and specifically where its leverage is **thin**, not only where it is strong.

Instruct all three to use the [SKILL.md](SKILL.md) vocabulary and the project's own domain terms. Without that, the proposals name the same thing three ways and cannot be compared.

## 3. Judge

Feed all three proposals verbatim to the deciding agent (in `/propose`, the architect). Compare on:

- **Depth** — how much behaviour each buys per unit of interface the caller has to learn.
- **Locality** — where change, bugs, and verification concentrate under each shape.
- **Seam placement** — where the boundary lands, and whether a second adapter actually justifies it (one adapter is a hypothetical seam; two make it real).

Then **commit to one and say why**, hybridizing where a rival's element is genuinely better. A menu handed back to the user is a failed judgment — be opinionated. Record the chosen shape and the rejected ones with their reasons in `design.md` `## Decisions`; a rejected alternative with a stated reason is what stops the next change from re-proposing it.
