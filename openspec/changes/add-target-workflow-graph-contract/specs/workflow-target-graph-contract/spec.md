# workflow-target-graph-contract Specification

## ADDED Requirements

### Requirement: WorkflowProgram lifecycle and target workflow graph must be separate

WorkflowProgram MUST keep its own S0-S6 lifecycle distinct from the graph semantics of generated target workflows.

#### Scenario: Target workflow uses a domain graph

- **GIVEN** WorkflowProgram runs its develop flow through S1-S6
- **WHEN** the accepted `workflow-spec.yaml` defines a target `workflow_graph`
- **THEN** the target graph MAY use request-specific node ids and transitions
- **AND** it MUST NOT be required to mirror S1-S6.

### Requirement: Target workflow graph must be machine-verifiable

`workflow-spec.yaml.workflow_graph` MUST define enough structure for deterministic validation of nodes, transitions, entrypoints, templates, and outputs.

#### Scenario: Transition references an unknown node

- **GIVEN** `workflow_graph.transitions[*].to` references a node id
- **WHEN** that node id is not declared in `workflow_graph.nodes`
- **THEN** spec validation MUST fail.

### Requirement: Accepted spec must drive target assets

Generated target commands, skills, agents, hooks, and runtime assets MUST be declared in `workflow-spec.yaml.registry` before managed apply.

#### Scenario: Candidate bundle contains undeclared target asset

- **GIVEN** the candidate bundle contains `.claude/agents/reverser.md`
- **AND** `workflow-spec.yaml.registry.agents` does not declare that asset
- **WHEN** S5 validates generated artifacts
- **THEN** the validation MUST fail or warn according to the declared safety policy.

### Requirement: Confirmation must include concrete write plan

S3 confirmation MUST name the accepted graph, enabled/disabled optional capabilities, and target files that will be written.

#### Scenario: Broad confirmation lacks file list

- **GIVEN** the user only approves a vague summary
- **WHEN** the readback does not list target files to be written
- **THEN** WorkflowProgram MUST NOT enter managed apply.

### Requirement: Managed apply must provide recovery evidence

Managed apply MUST produce recovery evidence sufficient to explain how to undo or manually recover the last apply.

#### Scenario: Managed file was updated

- **GIVEN** a managed target file is updated
- **WHEN** managed apply succeeds
- **THEN** `managed-rollback-manifest.json` MUST record the before state or explain why automatic rollback is unavailable.

### Requirement: Reports must be versioned, classifiable, and redacted

Critical JSON and Markdown reports MUST include stable schema/error fields and MUST redact known sensitive values before user-shareable output.

#### Scenario: Report includes token-like content

- **GIVEN** runtime evidence contains a token-like value
- **WHEN** a user-shareable report is generated
- **THEN** the report MUST replace the sensitive value with a redacted placeholder.

### Requirement: Team plans are not execution evidence

Agent/team execution MUST require evidence beyond a team plan.

#### Scenario: Team plan exists without role outputs

- **GIVEN** `agent_team_contract.enabled=true`
- **AND** `team-plan.json` exists
- **BUT** role outputs, team events, and join summary are missing
- **WHEN** S5 validates team evidence
- **THEN** the team participation check MUST fail or warn according to provider capability.
