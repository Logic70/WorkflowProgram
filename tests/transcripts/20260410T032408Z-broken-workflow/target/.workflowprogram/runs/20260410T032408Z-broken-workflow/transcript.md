# Runtime Smoke Transcript

- Run ID: `20260410T032408Z-broken-workflow`
- Fixture: `broken-workflow`
- Entry skill: `workflowprogram-validate`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032408Z-broken-workflow/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032408Z-broken-workflow/target/.workflowprogram/runs/20260410T032408Z-broken-workflow --entry-skill workflowprogram-validate --request '验证当前项目中的 workflow 资产，并输出失败项、影响范围和修复优先级' --fixture broken-workflow --timeout 90 --json
```

## Stdout

```text
{
  "result": "FAIL",
  "failure_code": "EVIDENCE_FAILURE",
  "message": "Mock host detected broken workflow assets and stopped validation.",
  "is_error": true,
  "stage_history": [
    "validate"
  ],
  "stage_status": "failed",
  "current_stage": "validate",
  "next_action": "repair broken workflow assets and rerun validate",
  "generated_files": []
}
```

## Stderr

```text
<empty>
```
