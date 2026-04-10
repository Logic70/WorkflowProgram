# Runtime Validation Report

- Run root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-broken-workflow/target/.workflowprogram/runs/20260409T141503Z-broken-workflow`
- Target root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-broken-workflow/target`
- Fixture: `broken-workflow`
- Entry skill: `workflowprogram-validate`
- Observed result: `FAIL`
- Observed failure kind: `implementation`
- Observed failure code: `EVIDENCE_FAILURE`
- Final verdict: `FAIL`
- Final failure kind: `implementation`
- Final failure code: `S5_BOUNDARY_TARGET_ROOT_BOUNDARY_CHANGES`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Summary

Mock host detected broken workflow assets and stopped validation.

Judge override: observed `FAIL` / `EVIDENCE_FAILURE`, final `FAIL` / `S5_BOUNDARY_TARGET_ROOT_BOUNDARY_CHANGES`. Triggered by `boundary.target_root_boundary_changes`: Changed target-root paths=['.workflowprogram/runs/20260409T141503Z-broken-workflow/events.jsonl', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/mock-runtime-host.log', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/current-progress.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/milestones.jsonl', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/user-progress.md', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/stages/runner-summary.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/stages/s0-route.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/target-claude-before.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/target-root-before.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/state.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/workflow-spec.yaml', 'validation-report.md']; disallowed=['validation-report.md']

## Spec Source

- `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-broken-workflow/target/.workflowprogram/runs/20260409T141503Z-broken-workflow/workflow-spec.yaml`

## Entry Checks

- [PASS] `smoke_entry_invoked`: Observed smoke entry skill: workflowprogram-validate (source: `smoke.invocation`)
- [PASS] `declared_main_entry`: Declared main_entry=workflowprogram-validate; smoke entry=workflowprogram-validate (source: `test_contract.entry.main_entry`)
- [PASS] `required_arguments_present`: Request payload is non-empty. (source: `test_contract.entry.required_args`)

## Boundary Checks

- [PASS] `write_boundaries_reference`: Boundary contract must reference runtime_contract.write_boundaries. (source: `test_contract.boundary.write_boundaries_ref`)
- [PASS] `run_root_spec_boundary`: workflow-spec.yaml should be allowed in RUN_ROOT for control-plane execution. (source: `runtime_contract.write_boundaries.run_root_allow`)
- [FAIL] `target_root_boundary_changes`: Changed target-root paths=['.workflowprogram/runs/20260409T141503Z-broken-workflow/events.jsonl', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/mock-runtime-host.log', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/current-progress.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/milestones.jsonl', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/progress/user-progress.md', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/stages/runner-summary.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/stages/s0-route.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/target-claude-before.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/outputs/target-root-before.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/state.json', '.workflowprogram/runs/20260409T141503Z-broken-workflow/workflow-spec.yaml', 'validation-report.md']; disallowed=['validation-report.md'] (source: `runtime_contract.write_boundaries.target_root_allow`)
- [FAIL] `external_write_policy`: external_write_policy=deny; disallowed_changes=['validation-report.md'] (source: `test_contract.boundary.external_write_policy`)
- [INFO] `managed_overwrite_policy_observed`: managed_overwrite_policy=reject-unmanaged-overwrite; no managed conflicts were observed. (source: `test_contract.boundary.managed_overwrite_policy`)
- [INFO] `conflict_artifacts_preserved`: conflict_expectation=keep-candidate-and-report; no conflicts were observed. (source: `test_contract.boundary.conflict_expectation`)

## Flow Checks

- [PASS] `required_stages_executed`: Observed stage_history=['requirement', 'context', 'design', 'generate', 'validate']; missing=none (source: `test_contract.flow.required_stages`)
- [PASS] `terminal_condition_observed`: Observed stage_status=failed; expected=failed (source: `test_contract.flow.terminal_conditions`)
- [PASS] `skippable_stages_observed`: Present skippable stages=['<none>']; absent skippable stages=['lessons'] (source: `test_contract.flow.skippable_stages`)
- [INFO] `failure_recovery_target`: Expected recovery target=generate, but provider did not expose next_stage_on_failure. (source: `test_contract.flow.failure_recovery`)

## Artifacts Checks

- [PASS] `evidence:context.json`: context.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:state.json`: state.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:events.jsonl`: events.jsonl exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:transcript.md`: transcript.md exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:validation-runtime-report.md`: validation-runtime-report.md is generated by the S5 judge. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stdout.log`: outputs/stdout.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stderr.log`: outputs/stderr.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/runtime-provider-result.json`: outputs/runtime-provider-result.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-claude-before.json`: outputs/target-claude-before.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-claude-files.json`: outputs/target-claude-files.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-root-before.json`: outputs/target-root-before.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-root-files.json`: outputs/target-root-files.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/mock-runtime-host.log`: outputs/mock-runtime-host.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/plugin-build-manifest.json`: outputs/plugin-build-manifest.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stages/s5-validation-summary.json`: outputs/stages/s5-validation-summary.json is generated by the S5 judge. (source: `runtime_smoke.evidence`)
- [PASS] `evidence_reference`: evidence_ref=runtime_contract.required_evidence (source: `test_contract.artifacts.evidence_ref`)
- [PASS] `required_runtime_evidence`: Missing required_evidence=['<none>'] (source: `runtime_contract.required_evidence`)
- [PASS] `route_evidence_matches_invocation`: Observed route entry_skill=workflowprogram-validate; intent=validate; expected entry_skill=workflowprogram-validate; intent=validate (source: `outputs/stages/s0-route.json`)
- [PASS] `runner_summary_matches_observed`: Observed runner-summary entry_skill=workflowprogram-validate; status=FAIL; expected entry_skill=workflowprogram-validate; status=FAIL (source: `outputs/stages/runner-summary.json`)
- [INFO] `deliverable:validation-report.md`: Deliverable pattern validation-report.md; matched_paths=['validation-report.md']; changed_matches=['validation-report.md'] (source: `test_contract.artifacts.deliverables`)

## Failure Checks

- [PASS] `derived_failure_kind`: Derived failure_kind=implementation; raw failure_code=EVIDENCE_FAILURE (source: `judge.mapping`)
- [WARN] `implemented_now_coverage`: implemented_now=['none', 'environment']; observed=implementation (source: `test_contract.failure.implemented_now`)
- [PASS] `failure_kinds_reference`: failure_kinds_ref=runtime_contract.failure_kinds (source: `test_contract.failure.failure_kinds_ref`)
- [PASS] `environment_skip_reference`: environment_skip_ref=runtime_contract.environment_skip (source: `test_contract.failure.environment_skip_ref`)

