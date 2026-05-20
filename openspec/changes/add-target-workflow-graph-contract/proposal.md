# Add Target Workflow Graph Contract

## Problem

WorkflowProgram currently uses `S0..S6` as both the product lifecycle vocabulary and the default shape of generated workflow specs. That is useful for controlling WorkflowProgram itself, but it can make target workflows look like they must follow the same fixed S1-S6 template even when the user needs a domain-specific graph.

OpenCode v2 design work clarified a better split:

- WorkflowProgram itself keeps the current S0-S6 lifecycle for clarification, design, managed apply, validation, and lessons.
- The target workflow produced by WorkflowProgram can have its own user-defined graph.
- AI/user design stays flexible, but accepted `workflow-spec.yaml` remains the only machine-readable semantic source.

## Goals

- Keep WorkflowProgram's own S0-S6 lifecycle unchanged.
- Add a target-workflow graph contract to `workflow-spec.yaml`.
- Make `workflow-spec.md` the accepted human readback for the graph and write plan.
- Keep `workflow-view.md` and `workflow-maintenance.md` as derived reports.
- Require target assets to be declared before generation.
- Add validation that graph nodes, transitions, registry entries, outputs, and evidence agree.
- Strengthen managed apply with rollback/recover evidence.
- Add schema, error-code, remediation, and privacy redaction rules for generated reports.
- Make agent/team evidence rules explicit: a plan is not execution evidence.

## Non-Goals

- Do not remove S0-S6 from WorkflowProgram's own production lifecycle.
- Do not migrate OpenCode-specific runtime, package, cache, venv, hook, bridge, or CLI details.
- Do not replace the Claude marketplace installation model.
- Do not introduce standalone AI evidence that can bypass clarification, readback, confirmation, and spec validation.
- Do not replace the current `stages` section in one step; add `workflow_graph` first and validate it alongside existing fields.

## Expected Outcome

After this change, a target workflow can be designed as a domain-specific graph while WorkflowProgram still uses its existing S0-S6 control plane to produce and verify it. Generated target assets must be traceable to accepted spec declarations, managed writes must be recoverable, and reports must be stable enough for later tools to parse safely.
