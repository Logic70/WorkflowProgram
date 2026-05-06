# Design Source Lineage

## Layering

WorkflowProgram keeps two layers separate:

- Design source: human-reviewable artifacts produced by S1-S3.
- Machine projection: `workflow-spec.yaml`, generated views, generated assets, runtime wrappers, state, and S5 evidence.

The default lineage is:

```text
S1 request
  -> outputs/stages/s1-requirements.yaml
  -> outputs/stages/s2-context-findings.yaml
  -> outputs/stages/s3-design-highlevel.md
  -> outputs/stages/s3-design-lowlevel.md
  -> outputs/stages/s3-implementation-plan.md
  -> outputs/stages/acceptance-tests.yaml
  -> outputs/stages/traceability-matrix.json
  -> workflow-spec.yaml design_refs
  -> S4 managed assets
  -> S5 runtime/state/judge evidence
```

`workflow-spec.yaml` remains the runtime map. It may reference design source files through `design_refs`, but it should not embed the full design discussion.

## Design Artifacts

- `s1-requirements.yaml` contains requirement ids, source references, priority, statement, acceptance hints, and boundaries.
- `s2-context-findings.yaml` contains context findings linked to requirement ids.
- `s3-design-highlevel.md` explains target workflow purpose, actors, major nodes, inputs, outputs, and boundaries.
- `s3-design-lowlevel.md` expands node behavior, required fields, prompts, evidence, and validation rules.
- `s3-implementation-plan.md` decomposes the accepted design into implementation tasks.
- `acceptance-tests.yaml` defines verifiable acceptance cases linked to requirements.
- `traceability-matrix.json` links requirement ids to design nodes, generated assets, acceptance tests, and evidence paths.
- `node-designs/<node-id>.md` is optional and only used when a target node is complex enough to need local detailed design.

## Complex Node Rule

Complexity is handled at the target node layer, not by creating a second WorkflowProgram lifecycle. A node should receive a node-design file when it has non-trivial domain reasoning, multiple data transformations, tool/MCP dependency choices, or its own TDD/loop policy.

For example, a STRIDE workflow may have one complex `build_dfd` node with a dedicated node design describing repository reading, data-flow extraction, trust-boundary inference, DFD evidence, and acceptance tests. That does not mean the generated target workflow itself runs WorkflowProgram S1-S6 internally.

## Node And Agent Policy

Node is a workflow-graph execution unit. Agent is an optional capability/persona assignment. A node only needs a distinct agent when the task needs specialized expertise, independent context boundaries, parallel review, or ownership separation.

## Verification

Validation happens in three layers:

- Spec validation rejects unsafe or inconsistent `design_refs`.
- Runner state validation accepts explicit design-source artifact kinds.
- S5 checks referenced design files exist, node-design ids match graph nodes, and requirement ids appear in the traceability matrix.

The initial S5 checks intentionally verify structural lineage. Deeper semantic consistency remains model-audited through the design review process.
