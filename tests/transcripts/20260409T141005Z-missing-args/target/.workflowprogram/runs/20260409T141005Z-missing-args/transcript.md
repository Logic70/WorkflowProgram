# Runtime Smoke Transcript

- Run ID: `20260409T141005Z-missing-args`
- Fixture: `missing-args`
- Entry skill: `workflowprogram-develop`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141005Z-missing-args/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141005Z-missing-args/target/.workflowprogram/runs/20260409T141005Z-missing-args --entry-skill workflowprogram-develop --request '' --fixture missing-args --timeout 90 --json
```

## Stdout

```text
{
  "result": "FAIL",
  "failure_code": "MISSING_ARGUMENT",
  "message": "Mock host rejected an empty request payload.",
  "is_error": true,
  "stage_history": [
    "requirement"
  ],
  "stage_status": "failed",
  "current_stage": "requirement",
  "next_action": "provide the required request arguments"
}
```

## Stderr

```text
<empty>
```
