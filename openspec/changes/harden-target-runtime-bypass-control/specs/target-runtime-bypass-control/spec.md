# target-runtime-bypass-control Specification

## ADDED Requirements

### Requirement: Managed-runtime commands are wrapper-only

When a target workflow declares `target_runtime_policy.mode=managed_runtime`, WorkflowProgram SHALL require the public entry command to invoke `.workflowprogram/runtime/workflow-entry.py` and SHALL reject command bodies that include node-by-node execution instructions, direct final output writes, report assembly steps, doctor invocation steps, manifest writes, latest marker writes, or other prompt-heavy bypass instructions.

#### Scenario: Prompt-heavy command is rejected

- **GIVEN** a target workflow with `target_runtime_policy.mode=managed_runtime`
- **AND** its main command both invokes `.workflowprogram/runtime/workflow-entry.py` and instructs the model to copy outputs into the final publish directory
- **WHEN** generated runtime validation runs
- **THEN** validation fails with a wrapper-only command error

### Requirement: Final publish state is finalizer-owned

WorkflowProgram SHALL require target final publish manifests to be produced by `target-runtime-finalizer.py`. A final publish directory SHALL NOT be considered valid when the final manifest says `COMPLETE/PASS` but the corresponding run root `target-state.json`, `node-results.json`, `artifact-provenance.json`, latest marker, or required reports do not agree for the same run.

#### Scenario: Forged COMPLETE manifest is rejected

- **GIVEN** a target workflow final output directory contains `run-manifest.json` with `status=COMPLETE`
- **AND** the referenced run root has `target-state.json.status=FAIL`
- **WHEN** target publish state validation runs
- **THEN** validation fails and the final output is not accepted as a trustworthy result

#### Scenario: Stale latest marker is rejected

- **GIVEN** a target workflow final output directory contains a finalizer-owned manifest for one run
- **AND** the latest marker references a different run or manifest
- **WHEN** target publish state validation runs
- **THEN** validation fails
