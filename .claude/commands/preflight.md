Run a full preflight check before submitting code for review or deployment.

Unlike /ship which is sequential (review → test → commit), preflight runs all checks IN PARALLEL for speed, then aggregates results into a single report. It does NOT commit.

## Step 1: Identify Scope

- Parse $ARGUMENTS as the target (default: changes since branching from main)
- Run `git diff main...HEAD --stat` to list affected files
- If no changes, stop and report "Nothing to check."

## Step 2: Parallel Checks (launch ALL at once)

Launch these agents simultaneously using Task tool (all in a SINGLE message):

**Agent 1 — Security Audit:**
> Scan all changed files for security vulnerabilities.
> Focus: injection, auth bypass, secrets exposure, memory safety, crypto weakness.
> Output one JSON per line: {"severity":"...","file":"...","line":...,"cwe":"...","description":"...","suggestion":"..."}
> If none: "No security issues detected."

**Agent 2 — Code Review (Logic + Style):**
> Review changed code for logic errors, edge cases, and style issues.
> Focus: off-by-one, null handling, error propagation, naming, type safety, documentation.
> Output one JSON per line: {"severity":"...","file":"...","line":...,"description":"...","suggestion":"..."}
> If none: "No code issues detected."

**Agent 3 — Test Verification:**
> Run the project's test suite (check CLAUDE.md for the test command).
> Check test coverage for changed files if coverage tool is available.
> Report: pass/fail, coverage %, uncovered lines in changed files.

**Agent 4 — Doc Check:**
> Verify docstrings/comments exist for all new public functions/classes.
> Check if README needs updating for public API changes.
> Report: list of missing documentation items.

## Step 3: Aggregate Results

Collect all agent results and produce a single report:

```
## Preflight Report

### Security: PASS / FAIL (N issues)
[list critical and warning items]

### Review:   PASS / FAIL (N issues)
[list critical and warning items]

### Tests:    PASS / FAIL (coverage: N%)
[failure details if any]

### Docs:     PASS / FAIL (N missing)
[list missing items]

### Overall Verdict: READY / NOT READY
```

**Overall is READY** only if: zero critical security issues AND tests pass.
Warnings and doc issues are reported but don't block.

Target: $ARGUMENTS (default: main...HEAD)
