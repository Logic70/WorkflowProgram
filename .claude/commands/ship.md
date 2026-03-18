Ship the current changes: review, test, and commit in one sequential pipeline.

## Step 1: Pre-check

- Run `git status` to confirm there are staged or unstaged changes
- If no changes found, stop and report "Nothing to ship."

## Step 2: Code Review (Fan-out)

Run a comprehensive code review on the current changes:

1. Get the diff: `git diff` (unstaged) or `git diff --cached` (staged)
2. Launch 4 parallel review agents using Task tool (all in a SINGLE message):
   - **Security reviewer** — scan for vulnerabilities (injection, auth, secrets, memory safety)
   - **Performance reviewer** — scan for bottlenecks (memory, I/O, algorithms, DB queries)
   - **Style reviewer** — scan for readability issues (naming, types, docs, structure)
   - **Logic reviewer** — scan for correctness bugs (edge cases, errors, concurrency, state)

   Each agent prompt must be FULLY INLINED in the Task call (subagents cannot read files from main context).
   Each agent outputs one JSON object per line: {"severity":"...","file":"...","line":...,"description":"...","suggestion":"..."}

3. Collect all agent outputs. Parse JSON lines, merge into a unified list sorted by severity (critical → warning → info).

**Gate**: If any CRITICAL issue is found, STOP here. Show the findings and ask the user whether to fix and retry, or force continue.

## Step 3: Run Tests

1. Run the project's test command (check CLAUDE.md for the test command)
2. If tests fail, analyze the failure and suggest a fix
3. Do NOT proceed to commit if tests fail — stop and report

**Gate**: Tests must pass to continue.

## Step 4: Generate Commit

1. Stage changes if not already staged (ask user for confirmation first)
2. Analyze changes and generate a Conventional Commits message:
   - `type(scope): subject` (50 char max)
   - Body explaining WHY (not what — the diff shows what)
3. Show the commit message and wait for user confirmation
4. Create the commit

## Step 5: Summary

Output a brief summary:
- Review: X issues found (Y critical, Z warnings, W info)
- Tests: passed / failed
- Commit: `<hash> <message>`

Ship target: $ARGUMENTS (default: all current changes)
