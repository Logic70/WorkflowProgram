# Harden Target Design Governance

## Summary

This change turns the previously optional target-workflow design-source model into a verifiable governance contract for newly developed target workflows.

The main product problem is naming and enforcement ambiguity:

- WorkflowProgram has its own product design documents, such as `workflowprogram-stage-highlevel-design.md` and `workflowprogram-stage-lowlevel-design.md`.
- Generated target workflows also produce design artifacts, currently named with terms such as `s3-design-highlevel.md` and `s3-design-lowlevel.md`.
- Current validation can check `design_refs` when declared, but `design_refs` is optional and does not force a complete requirement-to-design-to-spec-to-test-to-evidence chain.

## Goals

- Rename the target-workflow design-source vocabulary so it is distinct from WorkflowProgram's own product design vocabulary.
- Require new target workflows to declare a complete target design-source set in `workflow-spec.yaml`.
- Persist the target design-source archive under `TARGET_ROOT/.workflowprogram/design/source/**` so completed workflows remain self-describing after the original run evidence is no longer in context.
- Keep `workflow-spec.yaml` as the machine-readable runtime map and projection index, not a long-form design document.
- Make the target design lineage verifiable by validators and S5 judge.
- Require complex target workflow nodes to have dedicated target node-design documents or explicit exemptions.
- Require modification flows to preserve traceability from user feedback through change policy, design source, spec, tests, and runtime evidence.

## Non-Goals

- Do not force target workflows to use WorkflowProgram's internal `S1..S6` stage template as their business workflow.
- Do not remove the existing `workflow_graph` target-flow contract.
- Do not embed full target design overview/detail prose or WP product high-level/low-level prose inside `workflow-spec.yaml`.
- Do not require publish eligibility for every target workflow.
- Do not make Claude CLI agent-team execution fully deterministic in this change.

## User Impact

For new target workflows, WorkflowProgram will produce and validate explicitly named target-design artifacts:

- `target-requirements.yaml`
- `target-context-findings.yaml`
- `target-design-overview.md`
- `target-design-detail.md`
- `target-implementation-plan.md`
- `target-acceptance-tests.yaml`
- `target-traceability-matrix.json`
- `target-node-designs/<node-id>.md` when needed

Existing legacy artifact names remain readable during migration, but new WorkflowProgram output should use the target-prefixed names and archive those files into `.workflowprogram/design/source/**` during managed apply.
