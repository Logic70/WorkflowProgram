## ADDED Requirements

### Requirement: Workflow design SHALL identify required professional capabilities
When a target workflow depends on a domain-specific professional toolchain, the system SHALL make those capability dependencies explicit instead of leaving them hidden in prose or agent prompts.

#### Scenario: Reverse-engineering workflow declares host capabilities
- **WHEN** the requested workflow is for reverse engineering or binary analysis
- **THEN** the design output declares the required capability family, such as disassembly/decompilation tooling, debugger support, and any required Codex skills or MCP integrations

### Requirement: Host capability readiness SHALL be checked before finalizing the design
The system SHALL distinguish between workflow assets that belong in `TARGET_ROOT` and host capabilities that belong to the execution environment. Missing host capabilities MUST be reported as bootstrap work rather than silently assumed.

#### Scenario: Missing skill or MCP is detected
- **WHEN** the generated workflow depends on a skill, MCP server, or external binary that is not currently available in the host environment
- **THEN** the system records that dependency as a missing host capability and does not claim the workflow is fully ready

### Requirement: Host capability bootstrap SHALL require explicit approval and auditable evidence
The system SHALL treat skill installation, MCP configuration, and external-tool setup as explicit bootstrap actions. Those actions MUST be separately reviewable from normal `TARGET_ROOT/.claude/*` generation and MUST record what was installed, configured, or still missing.

#### Scenario: Bootstrap is proposed before install
- **WHEN** host capability gaps are found
- **THEN** the system produces a bootstrap plan that identifies the missing capabilities, the intended installation or configuration action, and the approval boundary before any host-environment mutation occurs

#### Scenario: Bootstrap evidence is persisted
- **WHEN** approved bootstrap actions complete
- **THEN** the run evidence includes a machine-readable summary of the capabilities checked, installed, configured, skipped, or still unresolved

### Requirement: Workflow contracts SHALL separate project assets from host capabilities
The machine-readable workflow contract SHALL represent host capability dependencies distinctly from `registry.commands`, `registry.skills`, and other target-project assets so that WorkflowProgram can validate readiness without confusing host setup with managed project writes.

#### Scenario: Host dependency is not modeled as a target asset
- **WHEN** a workflow depends on an external skill or MCP integration
- **THEN** the requirement is recorded under a host capability contract instead of pretending it is already a generated file under `TARGET_ROOT`
