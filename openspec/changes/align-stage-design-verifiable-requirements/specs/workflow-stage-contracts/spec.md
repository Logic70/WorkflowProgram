## ADDED Requirements

### Requirement: Stage evidence ownership SHALL be explicit and consistent
The system SHALL define stage evidence ownership consistently across HighLevel, LowLevel, and the runtime evidence model. `context.json`, `state.json`, and `events.jsonl` MUST be treated as runtime/control-plane evidence defined by the runtime evidence spec and preserved through `runtime_contract.required_evidence`. `validation-runtime-report.md` and `outputs/stages/s5-validation-summary.json` MUST remain S5 judgment artifacts. `transcript.md` MUST be treated as runtime execution evidence that S5 consumes but does not redefine.

#### Scenario: Control-plane evidence is declared in stage documents
- **WHEN** the stage documents enumerate minimum evidence or ownership for runtime evidence files
- **THEN** `state.json` and `events.jsonl` are assigned to runner/runtime evidence ownership rather than being described as S5-owned outputs

#### Scenario: S5 evidence ownership is declared
- **WHEN** the stage documents describe S5 outputs
- **THEN** they assign `validation-runtime-report.md` and `outputs/stages/s5-validation-summary.json` to S5 judgment responsibility and describe `transcript.md` as harness evidence consumed by S5

### Requirement: `S0` SHALL exit only after `target_root` exists
The system SHALL resolve `target_root` to an absolute path during `S0`. If the target directory does not exist, the system MUST create it before `S0` completes. Route evidence and stage progress evidence MUST record whether the directory already existed or was created during routing.

#### Scenario: Existing target root
- **WHEN** `S0` receives a target path that already exists
- **THEN** route evidence records the absolute path and marks the target as pre-existing before handing off to the next stage

#### Scenario: Missing target root
- **WHEN** `S0` receives a target path that does not yet exist
- **THEN** the system creates the directory before stage completion and records that creation in route or progress evidence

### Requirement: `S3` SHALL enforce approval before `S4`
For the `develop` flow, the system SHALL block transition from `S3` to `S4` until approval is resolved. Approval records MUST preserve the distinction between manual approval and automatic approval.

#### Scenario: Manual approval
- **WHEN** a user approves the `S3` design gate
- **THEN** the recorded approval state marks the gate as manually approved and permits transition to `S4`

#### Scenario: Automatic approval
- **WHEN** a CI rule or explicit auto-approval setting resolves the `S3` design gate
- **THEN** the recorded approval state marks the gate as auto-approved and permits transition to `S4`

### Requirement: Stage requirements SHALL be traceable to verification sources
Each stage `S0..S6` SHALL define a verifiable exit condition, minimum evidence, and the component or artifact that verifies the condition. HighLevel may stay coarse-grained, but it MUST not omit which artifact family proves stage completion.

#### Scenario: A stage defines exit conditions
- **WHEN** a stage is described in HighLevel and elaborated in LowLevel
- **THEN** both documents provide compatible exit conditions and a compatible evidence story that can be checked without relying on chat history

#### Scenario: A stage defines evidence verification
- **WHEN** a stage uses a script, validator, or judge as part of its completion rule
- **THEN** the documents identify that verification source explicitly instead of leaving completion as a free-form claim
