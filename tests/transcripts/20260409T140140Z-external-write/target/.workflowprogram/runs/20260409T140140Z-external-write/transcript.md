# Runtime Smoke Transcript

- Run ID: `20260409T140140Z-external-write`
- Fixture: `external-write`
- Entry skill: `workflowprogram-develop`
- Runtime provider: `fixture_host`
- Result: `PASS`
- Contract source: `fixture_preset`
- Contract categories: `boundary, artifacts, failure`

## Command

```bash
/usr/bin/python3 /mnt/d/Code/WorkflowProgram-CN/.claude/scripts/managed-assets.py apply-staged --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target --source-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.workflowprogram/runs/20260409T140140Z-external-write/outputs/candidate/.claude --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.workflowprogram/runs/20260409T140140Z-external-write --json
```

## Stdout

```text
{
  "generated_at": "2026-04-09T14:01:41Z",
  "target_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target",
  "source_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.workflowprogram/runs/20260409T140140Z-external-write/outputs/candidate/.claude",
  "run_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.workflowprogram/runs/20260409T140140Z-external-write",
  "manifest_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.workflowprogram/managed-files.json",
  "producer_version": "0.1.0",
  "summary": {
    "candidate_files": 4,
    "create": 4,
    "update": 0,
    "conflict": 0
  },
  "applied": [
    {
      "relative_path": ".claude/commands/generated-smoke.md",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.claude/commands/generated-smoke.md",
      "applied_sha256": "937c8a301478ccf1a57bf457e44642983c117c7f1fa79a1f5785e46c004d3fd4",
      "run_id": "20260409T140140Z-external-write"
    },
    {
      "relative_path": ".claude/rules/constraints.md",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.claude/rules/constraints.md",
      "applied_sha256": "6a9653e0e8754340b328589eb7a13d8374c3cf57b047ec52a1590f1d8c84c5f3",
      "run_id": "20260409T140140Z-external-write"
    },
    {
      "relative_path": ".claude/settings.json",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.claude/settings.json",
      "applied_sha256": "517fa393b839c915eb371b9b46cdd89cf78c401c995956e4e22765547e80f1ae",
      "run_id": "20260409T140140Z-external-write"
    },
    {
      "relative_path": ".claude/skills/generated-smoke/SKILL.md",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140140Z-external-write/target/.claude/skills/generated-smoke/SKILL.md",
      "applied_sha256": "2dabedf82e310b8b1591ae2072b35b803ff467e6a5b2ab4b036751523795689c",
      "run_id": "20260409T140140Z-external-write"
    }
  ],
  "conflicts": []
}
```

## Stderr

```text
<empty>
```
