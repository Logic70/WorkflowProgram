# Tasks

## 1. Contract And Design

- [x] 1.1 Add `target_runtime_policy` to the workflow spec schema and templates.
- [x] 1.2 Add `target_managed_runtime` to generated runtime capabilities.
- [x] 1.3 Update active design docs and user docs with managed target runtime semantics.

## 2. Runtime Generation

- [x] 2.1 Generate target runner wrappers that call `target-workflow-runner.py`.
- [x] 2.2 Generate target state validator wrappers that call `validate-target-runtime-state.py`.
- [x] 2.3 Add managed runtime markers and schema version to `runtime-manifest.json`.
- [x] 2.4 Require managed-runtime commands to be wrapper-only through validation.

## 3. Target Runner

- [x] 3.1 Add `target-workflow-runner.py`.
- [x] 3.2 Resolve graph entrypoints, transitions, and node order.
- [x] 3.3 Resolve node owners from registry and fail terminal on missing owners.
- [x] 3.4 Validate inputs, outputs, immutable paths, retries, and terminal conditions.
- [x] 3.5 Emit `target-state.json`, `target-events.jsonl`, `node-results.json`, `artifact-provenance.json`, and `target-runtime-summary.json`.

## 4. Runtime Validation And Judge

- [x] 4.1 Add `validate-target-runtime-state.py`.
- [x] 4.2 Extend `validate-generated-runtime.py` for managed-runtime markers, wrappers, manifest, and command wrapper checks.
- [x] 4.3 Extend S5 generated-runtime checks to surface managed-runtime failures.

## 5. Fixtures And Tests

- [x] 5.1 Update `valid-minimal.yaml` and runtime fixture command output for wrapper-only managed runtime.
- [x] 5.2 Add validator coverage for valid/invalid `target_runtime_policy`.
- [x] 5.3 Add unit or script tests for target runner pass and missing owner failure.
- [x] 5.4 Run spec validator fixtures, runtime smoke matrix, and repository validator.

## 6. Distribution

- [x] 6.1 Rebuild `dist/plugin`.
- [x] 6.2 Run final validation and commit the change.
