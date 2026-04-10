# Runtime Smoke Transcript

- Run ID: `20260409T140708Z-broken-workflow`
- Fixture: `broken-workflow`
- Entry skill: `workflowprogram-validate`
- Runtime provider: `command_adapter`
- Result: `PASS`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Command

```bash
python3 /mnt/d/Code/WorkflowProgram-CN/tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140708Z-broken-workflow/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140708Z-broken-workflow/target/.workflowprogram/runs/20260409T140708Z-broken-workflow --entry-skill workflowprogram-validate --request '验证当前项目中的 workflow 资产，并输出失败项、影响范围和修复优先级' --fixture broken-workflow --timeout 90 --json
```

## Stdout

```text
{
  "result": "PASS",
  "failure_code": "",
  "message": "Mock host completed workflow execution successfully.",
  "is_error": false,
  "stage_history": [
    "requirement",
    "context",
    "design",
    "generate",
    "validate",
    "lessons"
  ],
  "stage_status": "done",
  "current_stage": "lessons",
  "next_action": "complete",
  "generated_files": [
    ".claude/settings.json",
    ".claude/rules/constraints.md",
    ".claude/commands/example.md"
  ]
}
```

## Stderr

```text
<empty>
```
