## ADDED Requirements

### Requirement: Develop SHALL run an internal design-review agent before implementation

WorkflowProgram SHALL run an internal `workflow-design-reviewer` after S3 design sources and `workflow-spec.yaml` are produced and before S4 candidate generation / managed apply is allowed to affect the target project.

#### Scenario: New workflow design is reviewed before S4

- **WHEN** `workflowprogram-develop` creates a new workflow design
- **AND** S3 has produced high-level design, low-level design, acceptance tests, traceability, implementation plan, and `workflow-spec.yaml`
- **THEN** the system produces `RUN_ROOT/outputs/stages/design-review/design-review-packet.json`
- **AND** invokes the design-review role using that packet
- **AND** does not proceed to target writes until review closure is valid

#### Scenario: Existing workflow modification is reviewed with change context

- **WHEN** `change-context.json.change_policy_required=true`
- **THEN** the design-review packet includes `existing-workflow-readback.json`, `change-policy.json`, and `impact-analysis.json`
- **AND** the reviewer checks that the requested change, affected artifacts, and design/spec updates are consistent

### Requirement: Design review SHALL produce machine-checkable issues and closure

The design-review process SHALL output structured issue and closure artifacts that can be validated without relying on prose interpretation.

#### Scenario: Review finds blocking design issues

- **WHEN** the reviewer finds a design issue that can change workflow nodes, control flow, evidence, acceptance tests, write boundaries, or user success criteria
- **THEN** the issue is recorded in `design-review/issues.json`
- **AND** the issue has `blocking=true`, `severity`, `lens`, `affected_requirements`, `affected_artifacts`, `problem`, `why_it_matters`, and `required_fix`

#### Scenario: Review closes successfully

- **WHEN** all blocking issues are resolved
- **THEN** the system writes `design-review/closure.json`
- **AND** every resolved issue has `resolved_by` and `resolution_evidence`
- **AND** any remaining non-blocking issue is marked `accepted_risk` with a residual-risk explanation

### Requirement: S4 SHALL be blocked when design-review closure is absent or failed

WorkflowProgram SHALL prevent target writes when design-review closure evidence is missing, stale, invalid, or contains unresolved blocking issues.

#### Scenario: Gate validation fails

- **WHEN** `validate-design-review-gate.py` reports a failed gate
- **THEN** `workflow-entry.py` does not run managed apply
- **AND** `entry-orchestration-summary.json` records `status=BLOCKED`
- **AND** `failure_kind=design`
- **AND** `block_reason=design_review_unresolved`

#### Scenario: Generated target runtime runs its own workflow

- **WHEN** a generated target workflow invokes its target-side runtime wrapper
- **AND** it is not generating or applying WorkflowProgram-managed workflow assets
- **THEN** the product design-review gate is not required
- **AND** the target workflow continues to use its generated runtime contract

#### Scenario: Review reaches max rounds without closure

- **WHEN** the configured review round limit is reached
- **AND** at least one blocking issue remains open
- **THEN** the develop flow stops as `BLOCKED/design_review_unresolved`
- **AND** does not continue to S4 implementation or target writes

### Requirement: S5 SHALL audit design-review evidence

S5 judgment SHALL include design-review checks when develop runs with S3 design artifacts.

#### Scenario: Managed apply succeeded

- **WHEN** a develop run applies managed assets
- **THEN** S5 checks that design-review closure exists and passed before apply
- **AND** S5 fails with `failure_kind=design` if blocking issues were unresolved or closure is missing

#### Scenario: Semantic changes were made

- **WHEN** managed paths include `.claude/**` or `.workflowprogram/runtime/**`
- **THEN** S5 verifies those changes trace back to original requirements or resolved design-review issues
