## ADDED Requirements

### Requirement: `S5` SHALL be the workflow-level judgment stage
The system SHALL treat `workflowprogram-validate` and the S5 judge as the primary workflow-level validation path. The runner MUST NOT claim ownership of `validation-runtime-report.md` or `s5-validation-summary.json`.

#### Scenario: S5 verdict artifacts are produced
- **WHEN** validation completes
- **THEN** `validation-runtime-report.md` and `outputs/stages/s5-validation-summary.json` are produced by the S5 validation chain rather than by the runner alone

### Requirement: Validation SHALL consume `test_contract` and defer execution semantics to `runtime_contract`
The system SHALL derive S5 checks from `test_contract.entry`, `boundary`, `flow`, `artifacts`, and `failure`, while continuing to treat execution boundaries, required evidence, failure kinds, and environment skip semantics as `runtime_contract` concerns.

#### Scenario: Contract categories are traceable
- **WHEN** validation emits a verdict
- **THEN** the validation summary can explain which checks came from `entry`, `boundary`, `flow`, `artifacts`, and `failure`

### Requirement: Validation SHALL support feedback loops
The system SHALL support verdict-driven feedback: design failures route back toward design, implementation failures route back toward generation, environment skips remain distinguishable, and warnings continue into closure with traceable notes.

#### Scenario: Design defect routes back to design
- **WHEN** validation classifies a failure as a design issue
- **THEN** the defined flow allows returning to the design stage instead of treating the run as a terminal success
