# Runtime Smoke Transcript

- Run ID: `20260409T140056Z-managed-conflict`
- Fixture: `managed-conflict`
- Entry skill: `workflowprogram-develop`
- Runtime provider: `fixture_host`
- Result: `FAIL`
- Contract source: `fixture_preset`
- Contract categories: `boundary, artifacts, failure`

## Command

```bash
/usr/bin/python3 /mnt/d/Code/WorkflowProgram-CN/.claude/scripts/managed-assets.py apply-staged --target-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target --source-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/candidate/.claude --run-root /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict --json
```

## Stdout

```text
{
  "generated_at": "2026-04-09T14:01:04Z",
  "target_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target",
  "source_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/candidate/.claude",
  "run_root": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict",
  "manifest_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/managed-files.json",
  "producer_version": "0.1.0",
  "summary": {
    "candidate_files": 4,
    "create": 2,
    "update": 0,
    "conflict": 2
  },
  "applied": [
    {
      "relative_path": ".claude/commands/generated-smoke.md",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.claude/commands/generated-smoke.md",
      "applied_sha256": "937c8a301478ccf1a57bf457e44642983c117c7f1fa79a1f5785e46c004d3fd4",
      "run_id": "20260409T140056Z-managed-conflict"
    },
    {
      "relative_path": ".claude/skills/generated-smoke/SKILL.md",
      "action": "create",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.claude/skills/generated-smoke/SKILL.md",
      "applied_sha256": "2dabedf82e310b8b1591ae2072b35b803ff467e6a5b2ab4b036751523795689c",
      "run_id": "20260409T140056Z-managed-conflict"
    }
  ],
  "conflicts": [
    {
      "relative_path": ".claude/rules/constraints.md",
      "source_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/candidate/.claude/rules/constraints.md",
      "source_sha256": "4c33843cdd286c93c9e19acd529ad470ebb8bc03e4346cd716ec67a760f91a0a",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.claude/rules/constraints.md",
      "target_exists": true,
      "target_sha256": "f876c0a1ebc44b13502f4ecacd647007be9c5ee19128ad15bbc19e62f895533d",
      "ownership": null,
      "decision": "conflict-unmanaged-existing",
      "reason": "Target file exists but is not registered as managed.",
      "manifest_entry": null,
      "conflict_copy": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/conflicts/.claude/rules/constraints.md"
    },
    {
      "relative_path": ".claude/settings.json",
      "source_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/candidate/.claude/settings.json",
      "source_sha256": "517fa393b839c915eb371b9b46cdd89cf78c401c995956e4e22765547e80f1ae",
      "target_path": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.claude/settings.json",
      "target_exists": true,
      "target_sha256": "bbfb67c2aedeb5db6c377636864161beae83783a96c6614f9318e66eae8e1cf2",
      "ownership": null,
      "decision": "conflict-unmanaged-existing",
      "reason": "Target file exists but is not registered as managed.",
      "manifest_entry": null,
      "conflict_copy": "/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T140056Z-managed-conflict/target/.workflowprogram/runs/20260409T140056Z-managed-conflict/outputs/conflicts/.claude/settings.json"
    }
  ]
}
```

## Stderr

```text
<empty>
```
