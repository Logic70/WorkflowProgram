## Summary

Add an internal design-review agent gate between S3 design and S4 candidate generation / managed apply.

WorkflowProgram already has workflow design, validation, verifier, change-policy, and S5 judge mechanisms, but it does not currently have a dedicated reviewer that receives a fresh design packet and repeatedly challenges the S3 design before implementation begins. This change introduces that missing role and makes its closure machine-checkable.

## Motivation

Current develop behavior can turn user requirements into design sources, `workflow-spec.yaml`, candidate assets, and controlled writes. The weak point is that the same reasoning stream may create the design and proceed to implementation without an independent design challenge.

The desired behavior is:

- create or modify workflows only after S3 design has been reviewed from a fresh context;
- catch design omissions, requirement drift, layer confusion, over-engineering, and spec projection mismatches before assets are generated;
- require structured review issues and closure evidence rather than a prose "looks good" report;
- block target writes if blocking design-review issues remain unresolved.

## Scope

This change covers:

- a new internal `workflow-design-reviewer` agent role;
- review packet, issue ledger, round result, and closure output schemas;
- the S3 -> S4 control gate for both new workflow creation and change-policy based modification;
- deterministic validation of review closure before managed apply;
- S5 checks that verify design-review evidence was produced and consumed.

## Out Of Scope

- Replacing S5 judge or runtime smoke tests.
- Replacing `workflowprogram-develop` with a new lifecycle entry.
- Forcing every generated target workflow to use an agent team.
- Letting the design-review agent write target files or candidate assets directly.
- Infinite autonomous looping without a hard blocked state when closure cannot be reached.

