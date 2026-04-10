# Runtime Smoke Transcript

- Run ID: `20260410T032203Z-broken-workflow`
- Fixture: `broken-workflow`
- Entry skill: `workflowprogram-validate`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `fixture_preset`
- Contract categories: `entry, artifacts, failure`

## Command

```bash
python3 tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-broken-workflow/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-broken-workflow/target/.workflowprogram/runs/20260410T032203Z-broken-workflow --entry-skill workflowprogram-validate --request '验证当前项目中的 workflow 资产，并输出失败项、影响范围和修复优先级' --fixture broken-workflow --timeout 90 --json
```

## Stdout

```text
<empty>
```

## Stderr

```text
python3: can't open file '/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-broken-workflow/target/tools/mock_runtime_host.py': [Errno 2] No such file or directory
```
