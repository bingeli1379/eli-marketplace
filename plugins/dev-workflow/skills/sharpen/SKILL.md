---
name: sharpen
description: Rewrite a shallow or vague task so it asks for deeper work, not wider scope. Rewrites the prompt only; it does not do the task.
disable-model-invocation: true
argument-hint: "[the task to deepen; defaults to your last request]"
---

# Sharpen a Task

**Goal**: make the task deeper, not bigger. The same job, held to the standard a top practitioner of the field would hold it to.

The task is `$ARGUMENTS`, or the user's most recent request when empty. With neither, ask the user for the task and stop.

## Steps

1. Answer four questions about the task, a line or two each:
   1. What would a top professional in this field do here that the request does not ask for?
   2. What is the rawest material they would start from, instead of what has already been digested for the user (a summary, a dashboard, someone else's write-up)?
   3. Which specific methods and tools would they use?
   4. What, other than you or the user, would show the result is right (a test, a measurement, a source of record, an independent check)?
2. Rewrite the task so it asks for exactly that. Keep the user's goal and every choice that is theirs to make; a choice of theirs stays open in the rewrite rather than being decided.
3. Show the four answers and the rewritten task, then stop. The user runs the rewrite.

## Guardrails

- Write in the language the task was written in. Answers to the four questions name real methods and tools of the field, never generic advice.
