## ADDED Requirements

### Requirement: Agent-team orchestration SHALL remain an explicit opt-in mode
The system SHALL keep the default execution model simple and deterministic. Team-style orchestration MAY be used, but only when the workflow contract explicitly enables it and defines the required topology.

#### Scenario: Default flow does not imply team mode
- **WHEN** a workflow spec does not explicitly declare agent-team orchestration
- **THEN** validation and execution treat the workflow as a non-team flow rather than inferring team behavior from prompt text

### Requirement: Agent-team contracts SHALL declare roles, ownership, and coordination rules
When team orchestration is enabled, the workflow contract SHALL define the participating roles, their ownership boundaries, permitted fan-out, and the join or review rule used to merge results.

#### Scenario: Team contract is machine-readable
- **WHEN** a workflow enables agent-team mode
- **THEN** the spec records each team role, its responsibility, its output expectation, and the join or approval rule that governs the team result

### Requirement: Agent-team execution SHALL leave verifiable runtime evidence
The system SHALL not treat team orchestration as a prompt-only convention. Runtime evidence MUST make the participating team roles, fan-out/join points, and accepted outputs visible enough for validation.

#### Scenario: Team execution can be audited
- **WHEN** a team-enabled workflow completes
- **THEN** the run evidence shows which team roles executed, what outputs they produced, and how the final accepted result was selected or merged

### Requirement: Agent-team validation SHALL enforce declared limits
If a workflow declares agent-team topology, validation SHALL check that execution stayed within the declared fan-out limit, respected ownership boundaries, and satisfied the declared join policy.

#### Scenario: Team execution exceeds declared fan-out
- **WHEN** a team-enabled workflow fans out beyond its declared limit
- **THEN** validation reports a contract failure instead of treating the run as a clean success
