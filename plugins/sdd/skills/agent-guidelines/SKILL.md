---
name: agent-guidelines
description: >
  Universal behavioral guidelines for ALL agents. Covers coding discipline (think before coding,
  simplicity first), exhaustive scanning (zero misses), language conventions, and spec-driven input rules.
  MUST be loaded when: dispatching any agent for implementation, review, or analysis tasks.
user-invocable: false
---

# Agent Guidelines

**Universal rules for every agent in the team. Internalize these before starting any task.**

## Coding Discipline

### 1. Think Before Coding

Surface assumptions and uncertainties — do NOT proceed silently with interpretations.

- **State your assumptions explicitly** before implementing. If uncertain, ask or flag it.
- **Present multiple interpretations** when a requirement is ambiguous — do NOT silently pick one.
- **Suggest simpler approaches** when the proposed approach seems over-engineered.
- **Stop and name the confusion** when something is unclear, rather than guessing.

### 2. Simplicity First

Minimum code that solves the stated problem. Nothing speculative.

- Do NOT add features beyond what was requested.
- Do NOT create abstractions for single-use code.
- Do NOT add unrequested flexibility or configurability.
- Do NOT add error handling for scenarios that cannot happen.

Self-check: *"Would a senior engineer call this overcomplicated?"*

## Exhaustive Scanning (Zero Misses)

**ZERO MISSES (highest priority):** Before acting on any task, exhaustively scan all files in scope. No scope specified → scan entire project. Scope specified → every file within it. Open and read files to confirm — never rely on filename guessing alone.

## Language

- **Output**: Traditional Chinese
- **Code, comments, and documentation**: English

## Spec-Driven Input

When receiving spec artifacts from `/apply`:

1. Read assigned `specs/<capability>/spec.md` files — WHEN/THEN scenarios are your acceptance criteria
2. Follow `design.md` decisions exactly — do NOT deviate from chosen approaches
3. Implement tasks from `tasks.md` in order, each scoped to one commit
4. Do NOT ask questions — specs are complete. If genuinely ambiguous, skip and flag it
