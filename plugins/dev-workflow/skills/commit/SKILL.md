---
name: commit
description: Use when committing staged changes or when the user asks to commit, write a commit message, or run /commit.
---

# Commit Message Generation

**Type**: Automated dev workflow
**Goal**: Generate a commit message following Conventional Commits and execute the commit

## Rules
- Write in English
- Only inspect Changes/Staged Changes to generate the message
- Only describe technical content

### Format
```
<type>: <title>

<body>
```

### Types
| Type | Purpose |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no feature/fix) |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `style` | Formatting, whitespace |
| `chore` | Maintenance, dependencies |
| `ci` | CI/CD changes |
| `build` | Build system changes |

### Description Rules
- Imperative mood: "add" not "added"
- Lowercase first letter
- No period at the end
- Keep under 50 characters

### Body
- Separate from title with blank line
- Wrap at 72 characters
- Explain "what" and "why", not "how"
- Skip for self-explanatory changes

### DO NOT
- Use past tense ("added", "fixed")
- Write vague descriptions ("bug", "changes", "stuff")
- Add promotional or attribution blocks
