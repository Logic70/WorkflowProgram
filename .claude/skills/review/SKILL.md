---
name: review
description: Run parallel multi-agent code review on current changes
disable-model-invocation: true
---

Run a code review on the current changes using 4 specialized agents in parallel.

## Step 1: Get the diff

Run `git diff $ARGUMENTS` to get the changes to review.
If $ARGUMENTS is empty, default to `git diff` (unstaged changes).
If the diff is empty, stop and report "No changes to review."

Capture the FULL diff output — this is what the agents will review.

## Step 2: Fan-out — 4 parallel review agents

Launch exactly 4 Task tool calls IN PARALLEL (in a single message). Each Task must:
- Use subagent_type: "general-purpose"
- Include the COMPLETE agent prompt below (do NOT tell the agent to read a file)
- Append the full diff content at the end of the prompt

**Task 1 — Security:**
> You are a security expert. Focus ONLY on security vulnerabilities.
> Ignore style, performance, logic. Check for: injection attacks, authentication bypass,
> hardcoded secrets, memory safety issues, cryptographic weaknesses, input validation gaps.
> Output one JSON object per line (no code fences):
> {"severity":"critical|warning|info","file":"<path>","line":<n>,"description":"<issue>","suggestion":"<fix>"}
> If no issues: "No security issues detected."

**Task 2 — Performance:**
> You are a performance engineer. Focus ONLY on performance issues.
> Ignore security, style, logic. Check for: memory leaks, unnecessary allocations,
> O(n²) algorithms, N+1 queries, blocking I/O, missing caching, resource leaks.
> Output one JSON object per line (no code fences):
> {"severity":"critical|warning|info","file":"<path>","line":<n>,"description":"<issue>","suggestion":"<fix>"}
> If no issues: "No performance issues detected."

**Task 3 — Style:**
> You are a style reviewer. Focus ONLY on code style and readability.
> Ignore security, performance, logic. Check for: unclear names, missing type annotations,
> missing docstrings, magic numbers, deep nesting, import order, code duplication.
> Output one JSON object per line (no code fences):
> {"severity":"critical|warning|info","file":"<path>","line":<n>,"description":"<issue>","suggestion":"<fix>"}
> If no issues: "No style issues detected."

**Task 4 — Logic:**
> You are a logic reviewer. Focus ONLY on correctness.
> Ignore security, performance, style. Check for: off-by-one errors, null handling,
> error propagation, race conditions, state inconsistency, unreachable code, edge cases.
> Output one JSON object per line (no code fences):
> {"severity":"critical|warning|info","file":"<path>","line":<n>,"description":"<issue>","suggestion":"<fix>"}
> If no issues: "No logic issues detected."

## Step 3: Fan-in — collect and merge

Extract all JSON lines from each agent's response. Merge into a single list.
Sort by severity: critical first, then warning, then info.
Remove duplicates (same file + same line + similar description).

## Step 4: Report

Display a structured summary:

```
## Code Review Report

### Summary
- Security: N findings (X critical, Y warning, Z info)
- Performance: N findings
- Style: N findings
- Logic: N findings

### Critical Issues (must fix)
[list items]

### Warnings (should fix)
[list items]

### Info (consider)
[list items]

### Verdict: PASS / NEEDS_WORK / CRITICAL_ISSUES
```
