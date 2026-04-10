# Runtime Smoke Transcript

- Run ID: `20260410T034705528864Z-existing-workflow`
- Fixture: `existing-workflow`
- Entry skill: `workflowprogram-iterate`
- Runtime provider: `command_adapter`
- Result: `PASS`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034705528864Z-existing-workflow/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034705528864Z-existing-workflow/target/.workflowprogram/runs/20260410T034705528864Z-existing-workflow --entry-skill workflowprogram-iterate --request '/workflowprogram-iterate evolve constraints from lessons' --fixture existing-workflow --timeout 90 --json
```

## Stdout

```text
{
  "result": "PASS",
  "failure_code": "",
  "message": "Mock host completed workflow audit successfully.",
  "is_error": false,
  "stage_history": [
    "lessons"
  ],
  "stage_status": "done",
  "current_stage": "lessons",
  "next_action": "complete",
  "generated_files": [
    "validation-report.md"
  ]
}
```

## Stderr

```text
<empty>
```
