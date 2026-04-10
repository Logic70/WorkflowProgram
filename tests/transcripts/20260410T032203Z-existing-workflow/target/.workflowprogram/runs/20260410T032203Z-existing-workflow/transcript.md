# Runtime Smoke Transcript

- Run ID: `20260410T032203Z-existing-workflow`
- Fixture: `existing-workflow`
- Entry skill: `workflowprogram-audit`
- Runtime provider: `command_adapter`
- Result: `FAIL`
- Contract source: `fixture_preset`
- Contract categories: `entry, flow, artifacts, failure`

## Command

```bash
python3 tools/mock_runtime_host.py invoke --plugin-root /mnt/d/Code/WorkflowProgram-CN/dist/plugin --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-existing-workflow/target --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-existing-workflow/target/.workflowprogram/runs/20260410T032203Z-existing-workflow --entry-skill workflowprogram-audit --request '审计当前项目中的 workflow 结构，并输出结构问题、模式偏离和下一步建议' --fixture existing-workflow --timeout 90 --json
```

## Stdout

```text
<empty>
```

## Stderr

```text
python3: can't open file '/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T032203Z-existing-workflow/target/tools/mock_runtime_host.py': [Errno 2] No such file or directory
```
