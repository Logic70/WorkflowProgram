Fast-track a hotfix: minimal checks, quick commit.

Skip style review, performance review, and doc check. Only security and tests gate the commit.

## Step 1: Create Hotfix Branch

- Run `git branch --show-current` to check current branch
- If on main, create and switch to `hotfix/<description>` branch (derive description from $ARGUMENTS or ask user)
- If already on a hotfix branch, continue on it

## Step 2: Security Check

Launch ONE Task for security review only:

> Scan the current diff for critical security issues.
> Focus: injection, auth bypass, secrets exposure, memory safety.
> Output one JSON per line: {"severity":"...","file":"...","line":...,"description":"...","suggestion":"..."}
> If none: "No security issues detected."

**Gate**: If any CRITICAL security issue is found, STOP. Show it and ask the user to fix before continuing.

## Step 3: Run Related Tests

1. Check `git diff` to identify changed files
2. Find and run ONLY tests related to the changed code (not the full suite)
3. If no related tests found, run the full test suite as fallback

**Gate**: Tests must pass to continue.

## Step 4: Quick Commit

1. Stage all changes
2. Generate commit message: `fix(scope): <description>` format
3. Show the commit message and wait for user confirmation
4. Create the commit

## Step 5: Summary

Output:
- Branch: `<branch name>`
- Security: PASS (N issues checked)
- Tests: passed (N tests run)
- Commit: `<hash> <message>`

Hotfix target: $ARGUMENTS (default: all current changes)
