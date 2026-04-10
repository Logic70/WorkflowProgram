## ADDED Requirements

### Requirement: Runtime evidence SHALL follow the Phase 3 evidence model
The system SHALL treat `context.json`, `state.json`, `events.jsonl`, `transcript.md`, and `validation-runtime-report.md` as the minimum runtime evidence model for dynamic validation runs.

#### Scenario: Minimum runtime evidence exists
- **WHEN** a runtime validation run completes or is skipped
- **THEN** the required runtime evidence files exist under `RUN_ROOT` unless the run failed before initialization

### Requirement: Stage progress SHALL be continuously materialized
The system SHALL maintain `current-progress.json`, `milestones.jsonl`, and `user-progress.md` under `RUN_ROOT/outputs/progress/` and use them as the source for user-visible progress reporting.

#### Scenario: Stage progress files are written
- **WHEN** a stage starts, checkpoints, and completes
- **THEN** the progress artifacts reflect current stage, recent milestones, and next action guidance

### Requirement: Required evidence SHALL be machine-checkable
The system SHALL declare minimum evidence through `runtime_contract.required_evidence` and the runner SHALL fail or downgrade the run when required evidence is missing.

#### Scenario: Missing evidence is detected
- **WHEN** a required evidence file is missing at the end of a run
- **THEN** the runner does not report the run as a clean success
