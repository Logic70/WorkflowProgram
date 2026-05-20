# Proposal

## Why

FreeSTRIDE exposed a gap in WorkflowProgram's target design governance: complex target workflow nodes can be required to have a `target-node-designs/<node-id>.md` file, but WorkflowProgram does not yet validate whether that file contains enough node-level executable design to guide implementation and review.

For workflows such as reverse engineering or STRIDE security testing, a single node can be as complex as a complete sub-workflow. The existing global target design overview/detail is useful, but it is too coarse to guarantee each complex node has clear inputs, outputs, ownership, tool usage, failure handling, evidence, and tests.

## What Changes

- Add a reusable target node design template under `workflow-spec-support`.
- Add `validate-target-node-design.py` to validate node-design Markdown against `workflow-spec.yaml.workflow_graph`.
- Extend target design governance and S5 judge to validate node-design content, not only file existence.
- Update prompts and docs so complex, looped, security-critical, reverse-engineering, or tool-heavy nodes must use the node design contract unless explicitly exempted.
- Update deterministic fixtures and unit tests to emit and validate the stronger node design contract.

## What Does Not Change

- WorkflowProgram's own control plane remains S0..S6.
- Target workflows remain free to use custom `workflow_graph.nodes`; they are not forced into S1..S6.
- `workflow-spec.yaml` remains the machine-readable runtime map and design-source index. It does not embed full node-design prose.
- Existing legacy node-design paths remain readable for migration, but new generated evidence should use `outputs/stages/target-node-designs/**`.

## Success Criteria

- Complex target nodes fail validation when their node-design file is missing or structurally incomplete.
- Valid node-design files prove alignment with node id, owner, template, gate, input refs, output refs, loop policy, tests, and failure handling.
- S5 records node-design content validation as deterministic evidence.
- Existing smoke fixtures continue passing after deterministic mock node-design output is upgraded.
