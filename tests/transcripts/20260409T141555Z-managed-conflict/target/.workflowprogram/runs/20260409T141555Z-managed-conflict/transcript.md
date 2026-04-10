# Runtime Smoke Transcript

- Run ID: `20260409T141555Z-managed-conflict`
- Fixture: `managed-conflict`
- Entry skill: `workflowprogram-develop`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141555Z-managed-conflict/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141555Z-managed-conflict/target/.workflowprogram/runs/20260409T141555Z-managed-conflict --entry-skill workflowprogram-develop --request '触发 managed-conflict 验证路径' --fixture managed-conflict --timeout 90 --json
```

## Stdout

```text
{
  "result": "FAIL",
  "failure_code": "CONFLICT_FAILURE",
  "message": "Mock host detected a managed asset conflict and kept candidate copies.",
  "is_error": true,
  "stage_history": [
    "requirement",
    "context",
    "design",
    "generate",
    "validate"
  ],
  "stage_status": "failed",
  "current_stage": "generate",
  "next_action": "resolve managed conflicts and rerun generate",
  "generated_files": [
    ".claude/settings.json",
    ".claude/rules/constraints.md"
  ]
}
```

## Stderr

```text
<empty>
```
