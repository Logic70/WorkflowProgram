## ADDED Requirements

### Requirement: `S2` SHALL produce a structured context report
The system SHALL produce `RUN_ROOT/outputs/stages/s2-context-report.md` covering reusable assets, gaps, and naming guidance for the target project.

#### Scenario: Context report is complete
- **WHEN** `S2` completes successfully
- **THEN** the context report includes reusable assets, gaps, and naming guidance tied to paths under `TARGET_ROOT`

### Requirement: `S3` SHALL produce the machine-readable design contract
The system SHALL produce `workflow-spec.yaml` and `workflow-view.md`, and the YAML contract MUST include `runtime_contract` and `test_contract` with all required top-level sections.

#### Scenario: Design contract passes validation
- **WHEN** `S3` completes successfully
- **THEN** `validate-workflow-spec.py` accepts `workflow-spec.yaml` and `workflow-view.md` exists as the rendered view

### Requirement: `S3` SHALL enforce an approval gate before generation
For `develop`, `S3` SHALL block progression to `S4` until approval is resolved. The recorded state MUST distinguish `approved` from `auto-approved`.

#### Scenario: Manual approval is preserved
- **WHEN** the user approves a design
- **THEN** the recorded approval state is manual approval rather than auto approval

#### Scenario: Auto approval is preserved
- **WHEN** the flow is auto-approved by CI or explicit automation
- **THEN** the recorded approval state remains distinguishable from manual approval
