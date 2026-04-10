# Runtime Validation Report

- Run root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034845424710Z-existing-workflow/target/.workflowprogram/runs/20260410T034845424710Z-existing-workflow`
- Target root: `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034845424710Z-existing-workflow/target`
- Fixture: `existing-workflow`
- Entry skill: `workflowprogram-audit`
- Observed result: `PASS`
- Observed failure kind: `none`
- Observed failure code: `none`
- Final verdict: `PASS`
- Final failure kind: `none`
- Final failure code: `none`
- Contract source: `workflow-spec.yaml.test_contract`
- Contract categories: `entry, boundary, flow, artifacts, failure`

## Summary

Mock host completed workflow audit successfully.

## Spec Source

- `/mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034845424710Z-existing-workflow/target/.workflowprogram/runs/20260410T034845424710Z-existing-workflow/workflow-spec.yaml`

## Entry Checks

- [PASS] `smoke_entry_invoked`: Observed smoke entry skill: workflowprogram-audit (source: `smoke.invocation`)
- [PASS] `declared_main_entry`: Declared main_entry=workflowprogram-audit; smoke entry=workflowprogram-audit (source: `test_contract.entry.main_entry`)
- [PASS] `required_arguments_present`: Request payload is non-empty. (source: `test_contract.entry.required_args`)

## Boundary Checks

- [PASS] `write_boundaries_reference`: Boundary contract must reference runtime_contract.write_boundaries. (source: `test_contract.boundary.write_boundaries_ref`)
- [PASS] `run_root_spec_boundary`: workflow-spec.yaml should be allowed in RUN_ROOT for control-plane execution. (source: `runtime_contract.write_boundaries.run_root_allow`)
- [PASS] `target_root_boundary_changes`: Changed target-root paths=['.workflowprogram/runs/20260410T034845424710Z-existing-workflow/events.jsonl', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/mock-runtime-host.log', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/progress/current-progress.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/progress/milestones.jsonl', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/progress/user-progress.md', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/stages/runner-summary.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/stages/s0-route.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/stages/s6-lessons-delta.md', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/target-claude-before.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/target-root-before.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/state.json', '.workflowprogram/runs/20260410T034845424710Z-existing-workflow/workflow-spec.yaml', 'validation-report.md']; disallowed=['<none>'] (source: `runtime_contract.write_boundaries.target_root_allow`)
- [PASS] `external_write_policy`: external_write_policy=deny; disallowed_changes=['<none>'] (source: `test_contract.boundary.external_write_policy`)
- [INFO] `managed_overwrite_policy_observed`: managed_overwrite_policy=reject-unmanaged-overwrite; no managed conflicts were observed. (source: `test_contract.boundary.managed_overwrite_policy`)
- [INFO] `conflict_artifacts_preserved`: conflict_expectation=keep-candidate-and-report; no conflicts were observed. (source: `test_contract.boundary.conflict_expectation`)

## Flow Checks

- [PASS] `stage_history_available`: Observed stage_history=['validate', 'lessons'] (source: `runtime-provider.stage_history`)
- [PASS] `required_stages_executed`: Observed stage_history=['validate', 'lessons']; missing=none (source: `intent_flows.audit.required_stage_slots`)
- [PASS] `unexpected_stages_absent`: Observed stage_history=['validate', 'lessons']; allowed=['validate', 'lessons']; unexpected=['<none>'] (source: `intent_flows.audit.required_stage_slots+intent_flows.audit.optional_stage_slots`)
- [PASS] `stage_order_valid`: Observed stage_history=['validate', 'lessons']; allowed_order=['validate', 'lessons'] (source: `intent_flows.audit.required_stage_slots+intent_flows.audit.optional_stage_slots`)
- [PASS] `stage_status_available`: Observed stage_status=done (source: `runtime-provider.stage_status`)
- [PASS] `terminal_condition_observed`: Observed stage_status=done; expected=done (source: `test_contract.flow.terminal_conditions`)
- [PASS] `skippable_stages_observed`: Present skippable stages=['<none>']; absent skippable stages=['<none>'] (source: `intent_flows.audit.optional_stage_slots`)

## Artifacts Checks

- [PASS] `evidence:context.json`: context.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:state.json`: state.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:events.jsonl`: events.jsonl exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:transcript.md`: transcript.md exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:validation-runtime-report.md`: validation-runtime-report.md is generated by the S5 judge. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/progress/current-progress.json`: outputs/progress/current-progress.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/progress/milestones.jsonl`: outputs/progress/milestones.jsonl exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/progress/user-progress.md`: outputs/progress/user-progress.md exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stdout.log`: outputs/stdout.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stderr.log`: outputs/stderr.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/runtime-provider-result.json`: outputs/runtime-provider-result.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-claude-before.json`: outputs/target-claude-before.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-claude-files.json`: outputs/target-claude-files.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-root-before.json`: outputs/target-root-before.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/target-root-files.json`: outputs/target-root-files.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/mock-runtime-host.log`: outputs/mock-runtime-host.log exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stages/s6-lessons-delta.md`: outputs/stages/s6-lessons-delta.md exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/plugin-build-manifest.json`: outputs/plugin-build-manifest.json exists in RUN_ROOT. (source: `runtime_smoke.evidence`)
- [PASS] `evidence:outputs/stages/s5-validation-summary.json`: outputs/stages/s5-validation-summary.json is generated by the S5 judge. (source: `runtime_smoke.evidence`)
- [PASS] `evidence_reference`: evidence_ref=runtime_contract.required_evidence (source: `test_contract.artifacts.evidence_ref`)
- [PASS] `required_runtime_evidence`: Missing required_evidence=['<none>'] (source: `runtime_contract.required_evidence`)
- [PASS] `route_evidence_matches_invocation`: Observed route entry_skill=workflowprogram-audit; intent=audit; expected entry_skill=workflowprogram-audit; intent=audit (source: `outputs/stages/s0-route.json`)
- [PASS] `runner_summary_matches_observed`: Observed runner-summary entry_skill=workflowprogram-audit; status=PASS; expected entry_skill=workflowprogram-audit; status=PASS (source: `outputs/stages/runner-summary.json`)
- [PASS] `s6_lessons_delta_exists`: s6-lessons-delta.md exists at /mnt/d/Code/WorkflowProgram-CN/tests/transcripts/20260410T034845424710Z-existing-workflow/target/.workflowprogram/runs/20260410T034845424710Z-existing-workflow/outputs/stages/s6-lessons-delta.md (source: `S6.outputs/stages/s6-lessons-delta.md`)
- [PASS] `s6_lessons_delta_valid`: S6 lessons delta and user progress passed deterministic validation. (source: `validate-lessons-delta.py`)
- [PASS] `deliverable:validation-report.md`: Deliverable pattern validation-report.md; matched_paths=['validation-report.md']; changed_matches=['validation-report.md'] (source: `test_contract.artifacts.deliverables`)

## Failure Checks

- [PASS] `derived_failure_kind`: Derived failure_kind=none; raw failure_code=none (source: `judge.mapping`)
- [PASS] `implemented_now_coverage`: implemented_now=['none', 'environment']; observed=none (source: `test_contract.failure.implemented_now`)
- [PASS] `failure_kinds_reference`: failure_kinds_ref=runtime_contract.failure_kinds (source: `test_contract.failure.failure_kinds_ref`)
- [PASS] `environment_skip_reference`: environment_skip_ref=runtime_contract.environment_skip (source: `test_contract.failure.environment_skip_ref`)

