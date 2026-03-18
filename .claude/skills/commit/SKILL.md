---
name: commit
description: Generate a well-structured Conventional Commits message
disable-model-invocation: true
---

Analyze the current changes and generate a Conventional Commits message.

## Step 1: Get changes

Run `git diff --cached --stat` to see staged changes.
If nothing staged, run `git diff --stat` for unstaged changes and ask user if they want to stage all.

## Step 2: Analyze changes

Read the full diff to understand:
- What was changed (files, functions, logic)
- Why it was changed (fix bug? add feature? refactor?)
- What is the scope (which module/component)

## Step 3: Generate commit message

Format:
```
type(scope): subject (max 50 chars)

Body: explain WHY this change was made, not WHAT (the diff shows what).
Mention any trade-offs or decisions made.

Breaking changes or important notes if applicable.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `ci`, `build`

## Step 4: Confirm and commit

1. Show the generated commit message
2. Wait for user confirmation or edits
3. Run `git commit -m "<message>"` with the confirmed message

Target: $ARGUMENTS (optional: override commit type or scope)
