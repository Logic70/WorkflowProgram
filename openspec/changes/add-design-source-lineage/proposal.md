# Add Design Source Lineage

## Problem

WorkflowProgram can currently turn a user request into a target `workflow-spec.yaml`, but the source reasoning that connects the raw requirement to that machine projection is too easy to lose. This creates four concrete risks:

- Complex requests may jump from S1 directly into YAML without a reviewable design plan.
- `workflow-spec.yaml` can become overloaded with design prose even though it is primarily a runtime/control-plane map.
- Complex target nodes, such as STRIDE DFD construction or reverse-engineering analysis, may be under-specified or over-expanded into a second S1-S6 lifecycle.
- S5 can validate runtime files while missing whether requirement, context, design, implementation, acceptance tests, and evidence still line up.

## Goals

- Keep WorkflowProgram's own S1-S6 lifecycle unchanged.
- Add explicit design-source artifacts before `workflow-spec.yaml` is finalized.
- Treat `workflow-spec.yaml.design_refs` as a machine-readable reference map to design-source artifacts, not as the place for full design prose.
- Allow complex target workflow nodes to have optional node-level design files.
- Make node and agent assignment deliberate rather than one agent per node by default.
- Add deterministic runtime evidence and S5 checks so the design-source layer is verifiable.

## Non-Goals

- Do not require every generated workflow to use OpenSpec.
- Do not replace `stages`, `intent_flows`, or `workflow_graph` with a new graph engine.
- Do not put full high-level or low-level design prose inside `workflow-spec.yaml`.
- Do not require every target node to be implemented by an independent agent.
- Do not change the target runtime model from `shared-control-plane-wrapper`.

## Expected Outcome

Generated workflows have a reviewable chain from raw requirement to context findings, design source, implementation plan, acceptance tests, traceability matrix, `workflow-spec.yaml`, generated assets, and runtime evidence. Simple workflows stay lightweight, while complex nodes can opt into node-level design without complicating the global lifecycle.
