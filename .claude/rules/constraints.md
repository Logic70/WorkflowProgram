# WorkflowProgram Constraints

Source: extracted-workflow hardening and local-Claude validation.

## Repository Invariants

- ALWAYS keep `README.md`, `CLAUDE.md`, `lessons.md`, `validation-report.md`, and `.claude/rules/constraints.md` present.
- ALWAYS keep `.claude/settings.json` aligned with actual user-facing commands and skills.
- ALWAYS keep `.claude/contracts/` present once the repository exposes contract-aware validation.
- NEVER treat `.claude/settings.local.json` as shared workflow logic.

## Extracted Workflow Conventions

- ALWAYS treat a generated standalone workflow repository as another Claude workflow repository unless the spec explicitly says otherwise.
- ALWAYS register commands in `.claude/settings.json` as an object map: `commands.<name>.file`.
- ALWAYS store user-facing command definitions as Markdown files under `.claude/commands/*.md`.
- ALWAYS store user-facing skills as `SKILL.md` files under `.claude/skills/<skill-name>/`.
- NEVER generate standalone command JSON files such as `.claude/commands/<name>.json` unless the target runtime contract explicitly requires JSON and the spec calls that out.
- NEVER switch `settings.json` to an array-based registration format when the target repository is Claude-compatible.
- ALWAYS declare the extraction target path and the expected write boundary before asking Claude to create files.
- ALWAYS mention `--add-dir <path>` or an equivalent workspace-expansion mechanism when the target output directory is outside the current Claude workspace.

## Command Design

- ALWAYS give each user-facing command a `Usage` section.
- ALWAYS structure user-facing commands as numbered stages with `Goal` and `Verify`.
- ALWAYS keep command frontmatter fields in sync with `.claude/contracts/command.schema.json`.
- ALWAYS declare dependencies and write targets explicitly in command frontmatter.
- ALWAYS checkpoint long-running workflow stages to disk before waiting for a final summary.
- ALWAYS consider non-interactive (CI/CD) mode when designing gates: support pre-approval via prompt parameters or environment variables.
- ALWAYS include toolchain degradation strategy in Stage 3 design when the workflow depends on external tools.
- ALWAYS provide structured methodology (Step 1/2/3...) for AI agents, not just "focus areas" lists.
- ALWAYS distinguish "append-only logs" (lessons.md, not read) from "session buffers" (session-findings.md, read/write).
- ALWAYS clone audit targets into project-internal paths (e.g., ./target-code/) to ensure workspace accessibility.
- NEVER exceed 4 parallel agents in one fan-out stage.
- NEVER require runtime subagents to load external agent files when prompts can be inlined or summarized in the command itself.

## Skill and Agent Design

- ALWAYS give every `SKILL.md` the fields `name`, `description`, and `version`.
- ALWAYS mark non-user-facing helper skills with `internal: true`.
- ALWAYS make reviewer and validator outputs structurally explicit.
- ALWAYS tag each finding with its source (tool name or AI agent) in audit-style workflows, to enable confidence assessment.
- NEVER leave command-critical support assets outside version control.

## Validation

- ALWAYS update `.claude/scripts/validate-workflow.ps1` when contracts or command metadata change.
- ALWAYS check external toolchain availability in validation scripts (informational warnings, non-blocking).
- ALWAYS keep `.claude/scripts/smoke-test-workflow.ps1` passing for registered commands.
- ALWAYS validate AI-written structured artifacts with a real parser before treating them as final outputs.
- ALWAYS record structural refactors and local-Claude test findings in `validation-report.md`.
- ALWAYS configure lightweight hooks (PostToolUseFailure, Stop) for error logging and progress tracking to reduce AI text output.
- NEVER add heavyweight shared hooks without documenting runtime cost and intent.
