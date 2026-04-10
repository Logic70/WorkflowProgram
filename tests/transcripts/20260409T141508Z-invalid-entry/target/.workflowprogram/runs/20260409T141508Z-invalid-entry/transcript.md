# Runtime Smoke Transcript

- Run ID: `20260409T141508Z-invalid-entry`
- Fixture: `invalid-entry`
- Entry skill: `missing-workflowprogram-entry`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141508Z-invalid-entry/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141508Z-invalid-entry/target/.workflowprogram/runs/20260409T141508Z-invalid-entry --entry-skill missing-workflowprogram-entry --request '验证非法入口时是否被正确拒绝' --fixture invalid-entry --timeout 90 --json
```

## Stdout

```text
{
  "result": "FAIL",
  "failure_code": "STRUCTURE_FAILURE",
  "message": "Mock host rejected an unknown workflow entry.",
  "is_error": true,
  "stage_history": [],
  "current_stage": "requirement",
  "next_action": "register the missing entry and rerun"
}
```

## Stderr

```text
<empty>
```
