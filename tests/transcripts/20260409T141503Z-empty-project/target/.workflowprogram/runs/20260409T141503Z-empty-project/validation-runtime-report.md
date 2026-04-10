# Runtime Validation Report

- Run root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-empty-project/target/.workflowprogram/runs/20260409T141503Z-empty-project`
- Target root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-empty-project/target`
- Fixture: `empty-project`
- Entry skill: `workflowprogram-develop`
- Observed result: `PASS`
- Observed failure kind: `none`
- Observed failure code: `none`
- Final verdict: `FAIL`
- Final failure kind: `implementation`
- Final failure code: `S5_BOUNDARY_MANAGED_OVERWRITE_POLICY_OBSERVED`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Summary

Mock host completed workflow execution successfully.

Judge override: observed `PASS` / `none`, final `FAIL` / `S5_BOUNDARY_MANAGED_OVERWRITE_POLICY_OBSERVED`. Triggered by `boundary.managed_overwrite_policy_observed`: managed_overwrite_policy=reject-unmanaged-overwrite; unexpected managed changes=['.claude/commands/example.md', '.claude/rules/constraints.md']

## Spec Source

- `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260409T141503Z-empty-project/target/.workflowprogram/runs/20260409T141503Z-empty-project/workflow-spec.yaml`

## Entry Checks

- [PASS] `smoke_entry_invoked`: Observed smoke entry skill: workflowprogram-develop (source: `smoke.invocation`)
- [PASS] `declared_main_entry`: Declared main_entry=workflowprogram-develop; smoke entry=workflowprogram-develop (source: `test_contract.entry.main_entry`)
- [PASS] `required_arguments_present`: Request payload is non-empty. (source: `test_contract.entry.required_args`)

## Boundary Checks

- [PASS] `write_boundaries_reference`: Boundary contract must reference runtime_contract.write_boundaries. (source: `test_contract.boundary.write_boundaries_ref`)
- [PASS] `run_root_spec_boundary`: workflow-spec.yaml should be allowed in RUN_ROOT for control-plane execution. (source: `runtime_contract.write_boundaries.run_root_allow`)
- [PASS] `target_root_boundary_changes`: Changed target-root paths=['.claude/commands/example.md', '.claude/rules/constraints.md', '.claude/settings.json', '.workflowprogram/runs/20260409T141503Z-empty-project/events.jsonl', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/candidate/.claude/settings.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/managed-change-plan.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/managed-change-result.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/mock-runtime-host.log', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/progress/current-progress.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/progress/milestones.jsonl', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/progress/user-progress.md', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/stages/runner-summary.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/stages/s0-route.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/target-claude-before.json', '.workflowprogram/runs/20260409T141503Z-empty-project/outputs/target-root-before.json', '.workflowprogram/runs/20260409T141503Z-empty-project/state.json', '.workflowprogram/runs/20260409T141503Z-empty-project/workflow-spec.yaml']; disallowed=['<none>'] (source: `runtime_contract.write_boundaries.target_root_allow`)
- [PASS] `external_write_policy`: external_write_policy=deny; disallowed_changes=['<none>'] (source: `test_contract.boundary.external_write_policy`)
- [PASS] `managed_candidate_sources_present`: Missing managed candidate source_path=['<none>'] (source: `outputs/managed-change-plan.json`)
- [FAIL] `managed_overwrite_policy_observed`: managed_overwrite_policy=reject-unmanaged-overwrite; unexpected managed changes=['.claude/commands/example.md', '.claude/rules/constraints.md'] (source: `test_contract.boundary.managed_overwrite_policy`)
- [INFO] `conflict_artifacts_preserved`: conflict_expectation=keep-candidate-and-report; no conflicts were observed. (source: `test_contract.boundary.conflict_expectation`)

## Flow Checks

- [PASS] `stage_history_available`: Observed stage_history=['requirement', 'context', 'design', 'generate', 'validate', 'lessons'] (source: `runtime-provider.stage_history`)
- [PASS] `required_stages_executed`: Observed stage_history=['requirement', 'context', 'design', 'generate', 'validate', 'lessons']; missing=none (source: `test_contract.flow.required_stages`)
- [PASS] `stage_status_available`: Observed stage_status=done (source: `runtime-provider.stage_status`)
- [PASS] `terminal_condition_observed`: Observed stage_status=done; expected=done (source: `test_contract.flow.terminal_conditions`)
- [PASS] `skippable_stages_observed`: Present skippable stages=['lessons']; absent skippable stages=['<none>'] (source: `test_contract.flow.skippable_stages`)

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
- [PASS] `evidence:outputs/managed-change-plan.json`: outputs/managed-change-plan.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/managed-change-result.json`: outputs/managed-change-result.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/mock-runtime-host.log`: outputs/mock-runtime-host.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/plugin-build-manifest.json`: outputs/plugin-build-manifest.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stages/s5-validation-summary.json`: outputs/stages/s5-validation-summary.json is generated by the S5 judge. (source: `runtime_smoke.evidence`)
- [PASS] `evidence_reference`: evidence_ref=runtime_contract.required_evidence (source: `test_contract.artifacts.evidence_ref`)
- [PASS] `required_runtime_evidence`: Missing required_evidence=['<none>'] (source: `runtime_contract.required_evidence`)
- [PASS] `route_evidence_matches_invocation`: Observed route entry_skill=workflowprogram-develop; intent=develop; expected entry_skill=workflowprogram-develop; intent=develop (source: `outputs/stages/s0-route.json`)
- [PASS] `runner_summary_matches_observed`: Observed runner-summary entry_skill=workflowprogram-develop; status=PASS; expected entry_skill=workflowprogram-develop; status=PASS (source: `outputs/stages/runner-summary.json`)
- [PASS] `deliverable:.claude/settings.json`: Deliverable pattern .claude/settings.json; matched_paths=['.claude/settings.json']; changed_matches=['.claude/settings.json'] (source: `test_contract.artifacts.deliverables`)
- [PASS] `deliverable:.claude/rules/constraints.md`: Deliverable pattern .claude/rules/constraints.md; matched_paths=['.claude/rules/constraints.md']; changed_matches=['.claude/rules/constraints.md'] (source: `test_contract.artifacts.deliverables`)

## Failure Checks

- [PASS] `derived_failure_kind`: Derived failure_kind=none; raw failure_code=none (source: `judge.mapping`)
- [PASS] `implemented_now_coverage`: implemented_now=['none', 'environment']; observed=none (source: `test_contract.failure.implemented_now`)
- [PASS] `failure_kinds_reference`: failure_kinds_ref=runtime_contract.failure_kinds (source: `test_contract.failure.failure_kinds_ref`)
- [PASS] `environment_skip_reference`: environment_skip_ref=runtime_contract.environment_skip (source: `test_contract.failure.environment_skip_ref`)

