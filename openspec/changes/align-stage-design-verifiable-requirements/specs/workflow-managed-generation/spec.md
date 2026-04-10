## ADDED Requirements

### Requirement: `S4` SHALL generate candidates before touching target assets
The system SHALL generate workflow assets under `RUN_ROOT/outputs/candidate/.claude/` before any managed apply step touches `TARGET_ROOT/.claude/`.

#### Scenario: Candidate assets exist before apply
- **WHEN** `S4` reaches managed apply planning
- **THEN** the candidate asset tree already exists under `RUN_ROOT`

### Requirement: Managed apply SHALL protect user assets
The system SHALL use a managed apply plan and result contract. Unmanaged or drifted target files MUST not be silently overwritten. Conflicts MUST preserve candidate copies and produce machine-readable conflict results.

#### Scenario: Conflict is preserved instead of overwritten
- **WHEN** managed apply detects a conflicting target file
- **THEN** the target file is not silently overwritten and the candidate or conflict copy is preserved under `RUN_ROOT/outputs/`

### Requirement: `S4` SHALL run the control-plane transition loop
The system SHALL use the runner to persist state, events, and runner summaries for the generated workflow run. `state.json` MUST satisfy artifact enum validation before `S4` is considered complete.

#### Scenario: Runner control-plane evidence exists
- **WHEN** `S4` completes successfully
- **THEN** `state.json`, `events.jsonl`, and `outputs/stages/runner-summary.json` exist and the run state passes validation
