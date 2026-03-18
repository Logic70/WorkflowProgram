---
name: test
description: Run tests intelligently based on current changes
disable-model-invocation: true
---

Run tests related to the current changes. Analyze failures and suggest fixes.

## Step 1: Identify changed files

Run `git diff --name-only $ARGUMENTS` to list changed files.
If $ARGUMENTS is empty, default to unstaged changes.

## Step 2: Find related tests

For each changed file, look for corresponding test files:
- Same directory: `test_<name>.*` or `<name>.test.*` or `<name>_test.*`
- Test directory: `tests/test_<name>.*` or `__tests__/<name>.test.*`
- Use glob/grep to search if naming convention is unclear

## Step 3: Run tests

If related test files found:
- Run only those tests (use the project's test command from CLAUDE.md)

If no related tests found:
- Run the full test suite as fallback

Pass through any extra arguments: $ARGUMENTS

## Step 4: Analyze results

If all tests pass:
- Report: "All N tests passed."

If any test fails:
- Show the failure output
- Analyze the root cause
- Suggest a specific fix with code example
- Ask if user wants to apply the fix
