## ADDED Requirements

### Requirement: Generated workflows SHALL ship a deterministic runtime entry path
When WorkflowProgram delivers a target workflow that claims staged execution, the delivered target workflow SHALL include a deterministic runtime entry path instead of relying only on prompt ordering across generated commands and skills.

#### Scenario: Generated workflow includes an explicit runtime entry
- **WHEN** a `develop` run finishes successfully for a new target workflow
- **THEN** the managed outputs include a target-side runtime entry asset that defines the fixed invocation path for that workflow

### Requirement: Generated workflows SHALL enforce machine-readable state transitions
If a generated workflow declares stages, intent flows, approval gates, runtime evidence, or test contracts, it SHALL also ship a runner-backed or explicitly equivalent control-plane mechanism that persists and validates state transitions for the target workflow.

#### Scenario: Generated workflow persists target-side control-plane evidence
- **WHEN** the generated workflow executes through its target-side runtime
- **THEN** it records machine-readable state, transition, and verdict evidence that can be validated against the declared workflow contract

### Requirement: Generated workflow runtime assets SHALL be managed outputs
The runtime entry wrapper and runner-equivalent control-plane assets for a generated workflow SHALL be delivered as managed target assets rather than transient run-only files.

#### Scenario: Target runtime is tracked as managed output
- **WHEN** WorkflowProgram writes the generated workflow into `TARGET_ROOT`
- **THEN** the target-side runtime assets are covered by managed apply and appear in the managed manifest for that target workflow

### Requirement: Validation SHALL fail when generated workflows claim control-plane guarantees without shipping the enforcing runtime
Validation SHALL treat it as a contract gap if a generated workflow declares deterministic stage behavior but ships only declarative docs, prompts, or commands without the target-side runtime mechanism that actually enforces that behavior.

#### Scenario: Declarative-only generated workflow is not accepted as complete
- **WHEN** a generated workflow contains stage/test contracts but lacks a target-side runtime entry and control-plane mechanism
- **THEN** conformance review marks the capability as missing or failing instead of treating the workflow as fully implemented
