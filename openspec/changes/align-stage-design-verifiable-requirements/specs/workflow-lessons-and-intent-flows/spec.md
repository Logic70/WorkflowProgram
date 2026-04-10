## ADDED Requirements

### Requirement: HighLevel SHALL define all supported intent flows
The HighLevel design SHALL publish the normative stage chain for `develop`, `audit`, `iterate`, and `validate`.

#### Scenario: Non-develop flows are first-class in HighLevel
- **WHEN** a reviewer reads the HighLevel document
- **THEN** they can determine the stage chains for `audit`, `iterate`, and `validate` without consulting LowLevel

### Requirement: `S6` SHALL close the loop with reusable outputs
The system SHALL produce a lessons delta tied to the current `run_id` and `failure_kind`, and it SHALL summarize historical milestone results for the user-facing progress view at the end of a run.

#### Scenario: Lessons delta is attributable
- **WHEN** `S6` completes
- **THEN** `outputs/stages/s6-lessons-delta.md` includes the current run identifier and the failure classification or an explicit no-new-constraint result

### Requirement: Iteration intent SHALL remain tied to lessons-driven improvement
The `iterate` intent SHALL remain a lessons-driven or improvement-driven path rather than a hidden alias for `develop`.

#### Scenario: Iterate intent stays distinct
- **WHEN** the system routes a request to `workflowprogram-iterate`
- **THEN** the documented flow and closure outputs reflect lessons-driven iteration semantics rather than generic workflow creation
