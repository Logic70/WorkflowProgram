# target-runtime-finalizer Specification

## ADDED Requirements

### Requirement: Target publish policy schema

Workflow specs SHALL support an optional `target_publish_policy` section.

When `target_publish_policy.enabled=true`, validators SHALL require:

- `run_scoped_outputs_required=true`
- `atomic=true`
- safe relative `publish_root`, `latest_marker`, and `manifest_path`
- `latest_marker` and `manifest_path` under `publish_root`
- `required_run_artifacts` as a non-empty list
- `required_reports` as a list of `{path,status_field,pass_values}`
- `generated_runtime_contract.runtime_capabilities` containing `target_atomic_publish`

#### Scenario: publish policy lacks runtime capability

- Given a spec with `target_publish_policy.enabled=true`
- And `generated_runtime_contract.runtime_capabilities` lacks `target_atomic_publish`
- When `validate-workflow-spec.py` runs
- Then validation fails.

### Requirement: Run-scoped target outputs

When `target_publish_policy.enabled=true`, the target managed runner SHALL write declared file outputs under `RUN_ROOT/<output_ref>` before final publish.

#### Scenario: deterministic provider creates output

- Given a target graph node output `outputs/target-workflow/report.md`
- When `target-workflow-runner.py` runs with `fixture_host`
- Then `RUN_ROOT/outputs/target-workflow/report.md` exists
- And `TARGET_ROOT/outputs/target-workflow/report.md` does not exist until finalizer publish.

### Requirement: Finalizer owns final publish

`target-runtime-finalizer.py` SHALL publish current-run target outputs only after current-run state, node results, artifact provenance, and required reports pass.

#### Scenario: required report mismatch

- Given `target-state.json` is `PASS`
- And a required report has a non-pass status
- When the finalizer runs
- Then finalizer returns `FAIL`
- And `target-state.json.status` becomes `FAIL`
- And no final manifest is published.

#### Scenario: all evidence passes

- Given current-run state, nodes, provenance, and required reports pass
- When the finalizer runs
- Then final outputs are atomically published to `TARGET_ROOT/<publish_root>`
- And the finalizer writes current-run manifest and latest marker.
