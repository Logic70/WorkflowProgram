## ADDED Requirements

### Requirement: `S1` SHALL be a `develop`-only clarification stage
The system SHALL use `S1` only for the `develop` intent. `audit`, `iterate`, and `validate` flows MUST bypass `S1` unless a future requirement explicitly extends them.

#### Scenario: Develop request enters `S1`
- **WHEN** the routed intent is `develop`
- **THEN** the stage chain includes requirement clarification before context discovery and design

#### Scenario: Non-develop request bypasses `S1`
- **WHEN** the routed intent is `audit`, `iterate`, or `validate`
- **THEN** the stage chain does not require `S1`

### Requirement: `S1` SHALL produce a non-ambiguous workflow specification draft
The system SHALL produce `RUN_ROOT/workflow-spec.md` with explicit input, output, trigger mode, and quality gate sections. The file MUST not contain unresolved placeholders such as `TBD` or `待补`.

#### Scenario: Requirement draft passes quality gate
- **WHEN** `S1` completes successfully
- **THEN** `workflow-spec.md` exists and contains the required sections without unresolved placeholders

### Requirement: `S1` SHALL leave traceable clarification evidence
The system SHALL record at least one clarification milestone and one specification persistence milestone in progress evidence when `S1` is used.

#### Scenario: Clarification milestones are recorded
- **WHEN** `S1` runs
- **THEN** progress artifacts include milestones for clarification and specification persistence
