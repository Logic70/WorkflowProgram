## Summary

`workflowprogram-clean` is a maintenance command for explicitly cleaning artifacts owned by WorkflowProgram. It is intentionally conservative: the default mode only reports planned actions, and deletion requires `--apply`.

The command is not part of the S1-S6 workflow execution path. Its job is operational hygiene: recover from plugin-local Python dependency corruption, remove repository test noise, and prune old target workflow runs when the user chooses a retention policy.

## Scope Model

### Python Runtime Cache

When `--python-runtime` is selected, the command may delete:

- `${CLAUDE_PLUGIN_DATA}/python/site-packages`
- `${CLAUDE_PLUGIN_DATA}/python/site-packages.tmp`
- `${CLAUDE_PLUGIN_DATA}/python/bootstrap-state.json`
- `${CLAUDE_PLUGIN_DATA}/python/requirements.lock.txt`

The next `workflowprogram-python` invocation or SessionStart bootstrap recreates the dependency layer.

### Test Artifacts

When `--test-artifacts` is selected from a WorkflowProgram repository root, the command may delete:

- `tests/transcripts/20*/`
- `__pycache__/`
- `*.pyc`

It must not delete fixture truth:

- `tests/fixtures/**`
- `tests/spec-fixtures/**`
- `tests/expectations/**`

### Run History

When `--run-history` is selected, the command scans:

```text
TARGET_ROOT/.workflowprogram/runs/*
```

It may delete old run directories only when one of these policies is supplied:

- `--keep-last N`
- `--older-than-days N`

Safety rules:

- Always keep the newest run.
- Keep all runs retained by `--keep-last`.
- Skip paths that are not direct children of `.workflowprogram/runs`.
- Skip symlinked run directories.
- Treat missing or malformed metadata as sortable by filesystem mtime, not as permission to bypass retention.

## Explicit Non-Goals

The command shall not clean:

- Claude Code marketplace plugin cache under `~/.claude/plugins/cache`
- `.claude/history/`
- `.claude/memory/`
- `.codex/`
- `.env*`
- `.mcp.json`
- `TARGET_ROOT/.workflowprogram/bootstrap/**`

These paths are owned by the host, the user, or the target workflow environment rather than by WorkflowProgram cleanup policy.

## CLI Contract

```text
workflowprogram-clean [--plugin-root PATH] [--plugin-data PATH]
                      [--target-root PATH]
                      [--python-runtime]
                      [--test-artifacts]
                      [--run-history]
                      [--keep-last N]
                      [--older-than-days N]
                      [--apply]
                      [--json]
```

Default behavior:

- If no cleanup scope is supplied, report all discoverable scopes but do not delete.
- Without `--apply`, every destructive item is reported as `planned`.
- With `--apply`, allowed items are deleted and reported as `deleted`.

## Report Contract

The command prints a structured report:

```json
{
  "generated_at": "...",
  "dry_run": true,
  "scopes": ["python_runtime"],
  "items": [
    {
      "kind": "python_runtime",
      "path": ".../python/site-packages",
      "action": "delete",
      "status": "planned",
      "reason": "plugin-local dependency cache"
    }
  ],
  "summary": {
    "planned_delete_count": 1,
    "deleted_count": 0,
    "skipped_count": 0,
    "error_count": 0
  }
}
```

When `RUN_ROOT` is set, the same payload is also written to:

```text
RUN_ROOT/outputs/stages/cache-cleanup-report.json
```

## Safety Boundary

Every deletion candidate must be resolved before deletion and checked against the owning root:

- `${CLAUDE_PLUGIN_DATA}/python/**`
- `REPO_ROOT/tests/transcripts/20*/**`
- repository-local `__pycache__` and `*.pyc`
- `TARGET_ROOT/.workflowprogram/runs/*`

The implementation must refuse to delete symlinked run directories and paths outside the allowed root.
