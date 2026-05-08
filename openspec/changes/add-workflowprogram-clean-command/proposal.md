## Why

WorkflowProgram now has several rebuildable or high-churn local artifacts:

- plugin-local Python dependency caches under `${CLAUDE_PLUGIN_DATA}/python`
- repository test transcripts and Python bytecode caches
- target workflow run history under `TARGET_ROOT/.workflowprogram/runs`

The current implementation has partial self-healing for Python bootstrap state, but it does not provide a user-facing cleanup command, dry-run reporting, or a safe run-history pruning policy. Users therefore either leave stale artifacts indefinitely or delete directories manually, which risks losing audit evidence.

## What Changes

- Add a first-class `workflowprogram-clean` maintenance command.
- Keep the command outside the S1-S6 control plane; cleanup is user-initiated maintenance, not a required workflow stage.
- Implement dry-run by default and require `--apply` for destructive actions.
- Support three V1 scopes:
  - plugin Python runtime cache
  - repository test artifacts and Python bytecode
  - target workflow run history pruning by `--keep-last` or `--older-than-days`
- Never clean Claude Code plugin marketplace cache, user-local Claude/Codex state, `.env*`, `.mcp.json`, or project-local bootstrap assets by default.

## Capabilities

### New Capabilities

- `workflow-maintenance-cleanup`: Provides safe, explicit cleanup for WorkflowProgram-controlled caches and selected historical artifacts.

### Modified Capabilities

- `workflow-plugin-marketplace-installation`: Adds a maintenance command to reset plugin-local Python dependency state without reinstalling the plugin.
- `workflow-runtime-evidence`: Defines run-history pruning as an explicit user action with retention guards, not an automatic cleanup.

## Impact

- Adds plugin runtime files:
  - `.claude/scripts/clean-workflowprogram.py`
  - `.claude-plugin/root/bin/workflowprogram-clean`
- Updates build and validation to include the new command in `dist/plugin`.
- Adds regression coverage for dry-run, Python cache deletion, bytecode/test artifact deletion, and guarded run-history pruning.
- Documents cleanup behavior in README and plugin README.
