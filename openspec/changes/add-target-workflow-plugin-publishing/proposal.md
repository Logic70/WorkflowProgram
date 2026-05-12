## Why

WorkflowProgram can already create and modify target workflows, but there is no first-class way to publish a completed target workflow as a Claude Code marketplace plugin for other users.

The current release tooling and marketplace metadata describe the WorkflowProgram plugin itself. They do not answer:

- how a workflow created by `workflowprogram-develop` becomes an installable plugin;
- how publish eligibility is verified without relying on Codex-only capabilities;
- how GitHub ownership, authentication, validation, and install instructions are handled for external users;
- how publish stays independent from the design/develop lifecycle while still requiring develop evidence.

The result should be a Claude Code-native publish flow: the user can run it from Claude Code, it uses the user's GitHub account, and it produces marketplace-compatible plugin metadata and install instructions.

## What Changes

- Add a new independent publish lifecycle for target workflows that have fully completed `workflowprogram-develop`.
- Add a public `workflowprogram-publish` skill and command for Claude Code users.
- Define publish eligibility checks over target workflow design, runtime, managed asset, S5, and design-review evidence.
- Define a target workflow plugin package model for Claude Code marketplace consumption.
- Define GitHub publishing behavior that uses the user's authenticated GitHub account and never stores tokens.
- Define machine-readable publish evidence, validation results, and generated install instructions.
- Keep publishing separate from normal `develop`, `validate`, `audit`, and `iterate` flows.

## Capabilities

### New Capabilities

- `target-workflow-plugin-publishing`: Packages and publishes WorkflowProgram-generated target workflows as Claude Code marketplace plugins.

### Modified Capabilities

- `workflowprogram-entry-exposure`: Adds a dedicated publish command and skill without re-expanding the general command surface.
- `workflow-generated-runtime-orchestration`: Clarifies the runtime dependency model when a generated workflow is exported as a plugin.
- `workflow-change-policy`: Does not govern publish-only metadata changes unless publish modifies the target workflow itself.

## Impact

- Adds new source assets:
  - `.claude/skills/workflowprogram-publish/SKILL.md`
  - `.claude/commands/workflowprogram-publish.md`
  - publish helper scripts under `.claude/scripts/`
- Adds publish evidence under `RUN_ROOT/outputs/stages/publish/`.
- May add optional publish metadata under `TARGET_ROOT/.workflowprogram/publish/`.
- Adds documentation for publishing target workflows through GitHub marketplace repositories.
- Adds smoke fixtures for eligible, ineligible, validation-failed, and GitHub-auth-missing publish flows.
- Does not require Codex to run the publish flow.
