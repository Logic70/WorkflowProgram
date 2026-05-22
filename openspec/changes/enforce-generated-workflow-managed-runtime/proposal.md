# Proposal

## Why

WorkflowProgram already uses a deterministic product control plane for its own develop/audit/iterate/validate lifecycle, but generated target workflows can still expose prompt-heavy commands that ask the model to run stages manually. That makes `workflow_graph.nodes`, owner rules, output contracts, and retry/stop rules advisory instead of executable.

Complex generated workflows need the same control-plane discipline as WorkflowProgram itself: a command should start runtime code, runtime code should execute the target graph, and validators/judges should reject bypassed runs.

## What Changes

- Add `target_runtime_policy` as the machine-readable contract for generated target workflow runtime enforcement.
- Generate target-side wrappers that call a new shared `target-workflow-runner.py` instead of the product `workflow-runner.py`.
- Add target runtime state/evidence validators for node lifecycle and artifact provenance.
- Require managed-runtime target commands to be wrapper-only and to call `.workflowprogram/runtime/workflow-entry.py`.
- Extend generated-runtime validation and S5 checks so missing managed runtime markers or wrapper-only command evidence fails.
- Update templates, docs, and fixtures so newly generated workflows default to managed runtime.

## What Does Not Change

- WorkflowProgram's own S0..S6 lifecycle remains controlled by the existing product `workflow-entry.py` and `workflow-runner.py`.
- Target workflows are still free to define request-specific `workflow_graph.nodes`; they are not forced into S1..S6.
- V1 does not claim to globally block every Claude Code Bash/Write path. It makes the supported entry controlled and makes bypassed runs unable to earn clean PASS.
- Existing legacy target workflows can remain readable, but they are not considered managed-runtime compliant until regenerated or migrated.

## Success Criteria

- A generated target runtime can execute `workflow_graph.nodes` through code and emit `target-state.json`, `target-events.jsonl`, `node-results.json`, and `artifact-provenance.json`.
- Missing owner, missing outputs, gate failure, immutable-path mutation, or runtime bypass produces deterministic FAIL evidence.
- `validate-generated-runtime.py` rejects managed-runtime workflows whose runtime wrappers still point at the product runner or whose command remains prompt-heavy.
- Existing product smoke tests still pass, and target runtime smoke uses the new managed target runner.
