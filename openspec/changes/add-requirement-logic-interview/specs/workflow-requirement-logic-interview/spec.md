# workflow-requirement-logic-interview Specification

## ADDED Requirements

### Requirement: S1 SHALL use a layered requirement logic interview

S1 SHALL guide clarification through purpose, object model, process model, decision model, evidence model, acceptance model, and boundary model before treating a non-trivial request as design-ready.

#### Scenario: Complex request is clarified by logic lenses

- **GIVEN** a user asks for a complex workflow such as STRIDE testing
- **WHEN** S1 clarification runs
- **THEN** the clarification lead asks questions that identify objects, process steps, decisions, evidence, acceptance scenarios, and boundaries
- **AND** the resulting handoff is more specific than generic inputs/outputs and edge cases.

### Requirement: Each logic lens SHALL define task, content, objective, and exit criteria

Each of the seven S1 logic lenses SHALL define what it is responsible for, what content it captures, what downstream design decision it supports, and what condition allows the lens to be considered sufficiently clarified.

#### Scenario: Lens definition is complete

- **GIVEN** S1 uses the `evidence_model` lens
- **WHEN** the clarification lead records the lens state
- **THEN** the lens includes evidence items, evidence links, minimum evidence, confidence policy, and invalid evidence rules where applicable
- **AND** the lens can state whether it is complete, blocked, or deferred.

#### Scenario: Lens lacks design consequence

- **GIVEN** a lens question is recorded in `question-backlog.json`
- **WHEN** the question has no downstream impact on nodes, decisions, evidence, acceptance, or boundaries
- **THEN** it SHALL NOT count toward logic-depth coverage.

### Requirement: S1 SHALL maintain a question backlog

S1 SHALL maintain `RUN_ROOT/outputs/stages/question-backlog.json` for medium or higher complexity requests.

#### Scenario: Next question is selected

- **GIVEN** the current clarification state has an unclear decision model
- **WHEN** the clarification lead prepares the next user question
- **THEN** `question-backlog.json` records the selected question, its lens, why it matters, whether it blocks design, expected answer shape, and linked requirement ids.

### Requirement: Questions SHALL be design-consequential

S1 questions SHALL be narrow enough that different plausible answers can alter workflow nodes, decisions, evidence, acceptance tests, or boundaries.

#### Scenario: Generic question is insufficient

- **GIVEN** a request has `L` or `XL` complexity
- **WHEN** the only recorded questions are broad prompts such as "what edge cases should we consider?"
- **THEN** S1 validation MUST reject the clarification as shallow.

### Requirement: S1 SHALL produce a requirement logic map

S1 SHALL produce `RUN_ROOT/outputs/stages/requirement-logic-map.json` before a medium or higher complexity request can be design-ready.

#### Scenario: Logic map is complete enough for S3

- **GIVEN** S1 marks the request as design-ready
- **WHEN** S3 consumes the handoff
- **THEN** `requirement-logic-map.json` contains purpose, object, process, decision, evidence, acceptance, and boundary sections.

### Requirement: Requirement ids SHALL link to logic model elements

For non-trivial requests, each `REQ-*` SHALL link to relevant process, decision, evidence, acceptance, or boundary elements, unless explicitly deferred or informational.

#### Scenario: Requirement lacks evidence or acceptance links

- **GIVEN** `s1-requirements.yaml` contains `REQ-001`
- **AND** `REQ-001` is marked as a must-have behavior
- **WHEN** `requirement-logic-map.json` has no process, evidence, or acceptance links for `REQ-001`
- **THEN** S1 validation MUST fail for `M+` complexity.

### Requirement: Complexity SHALL control clarification depth

S1 SHALL classify requirement complexity and apply stricter logic-depth validation for `M`, `L`, and `XL` requests while keeping simple requests lightweight.

#### Scenario: Simple request remains lightweight

- **GIVEN** the user asks for a simple workflow asset update
- **WHEN** all core intent, output, and validation information is already clear
- **THEN** S1 MAY use a compact logic map and proceed after readback.

#### Scenario: XL request requires deeper modeling

- **GIVEN** the user asks for reverse engineering, STRIDE, compliance, migration repair, or TDD implementation workflow
- **WHEN** S1 reaches readback
- **THEN** the logic map MUST include workflow node candidates and acceptance scenarios.

### Requirement: S2 and S3 SHALL consume the logic map

S2 and S3 SHALL receive `requirement-logic-map.json` through `clarification-handoff.json`.

#### Scenario: Handoff includes logic map

- **GIVEN** S1 completed for an `M+` request
- **WHEN** `clarification-handoff.json` is written
- **THEN** it includes `logic_map_path`, `question_backlog_path`, and S2/S3 input summaries derived from the logic map.

### Requirement: Internal challenge roles SHALL rank weak logic lenses

Internal S1 challenge roles SHALL identify weak or missing logic lenses and propose follow-up questions, while the clarification lead remains the only user-facing role.

#### Scenario: Challenge finds missing evidence model

- **GIVEN** the draft has purpose and process but no evidence model
- **WHEN** internal challenge runs
- **THEN** the challenge report marks `evidence_model` as weak
- **AND** proposes design-consequential evidence questions for the lead.
