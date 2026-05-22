# workflow-generated-managed-runtime Specification

## ADDED Requirements

### Requirement: Generated target workflows declare managed runtime policy

Newly generated target workflows SHOULD declare `target_runtime_policy.mode=managed_runtime`, and when they do, `generated_runtime_contract.runtime_capabilities` MUST include `target_managed_runtime`.

#### Scenario: Managed runtime capability is missing

- **GIVEN** a workflow spec declares `target_runtime_policy.mode=managed_runtime`
- **AND** `generated_runtime_contract.runtime_capabilities` omits `target_managed_runtime`
- **WHEN** spec validation runs
- **THEN** validation MUST fail.

### Requirement: Managed runtime executes target graph through code

A managed-runtime generated target workflow MUST execute `workflow_graph.nodes` through target runtime code rather than relying on prompt-heavy command text as the lifecycle owner.

#### Scenario: Target runtime runs graph nodes

- **GIVEN** a generated target workflow declares `target_runtime_policy.mode=managed_runtime`
- **AND** a supported entry command invokes `.workflowprogram/runtime/workflow-entry.py`
- **WHEN** the target runtime runs with a deterministic provider
- **THEN** it MUST emit `target-state.json`, `target-events.jsonl`, `node-results.json`, and `artifact-provenance.json`
- **AND** successful outputs MUST include provenance that names the producing node and owner.

### Requirement: Managed runtime rejects missing owners and missing outputs

Target graph owner resolution and output contract checks MUST be terminal after the configured retry budget.

#### Scenario: Node owner is not registered

- **GIVEN** a target graph node declares an owner that cannot be resolved from registry or supported script ownership
- **WHEN** the managed runtime reaches that node
- **THEN** the run MUST finish as `FAIL`
- **AND** the failure MUST be recorded in target runtime evidence.

### Requirement: Managed runtime protects immutable runtime paths

Target graph execution MUST NOT write outputs under paths declared by `target_runtime_policy.immutable_during_run`.

#### Scenario: Graph output conflicts with immutable path

- **GIVEN** a target runtime policy declares `.claude/**` immutable
- **AND** a graph node declares `.claude/skills/example/SKILL.md` as an output
- **WHEN** spec validation runs
- **THEN** validation MUST fail before runtime execution.

### Requirement: Managed runtime commands are wrapper-only

When a target workflow declares managed runtime, its registered main command MUST invoke `.workflowprogram/runtime/workflow-entry.py` and MUST NOT contain prompt-heavy stage execution instructions.

#### Scenario: Main command contains stage prompt instructions

- **GIVEN** a generated target workflow declares `target_runtime_policy.mode=managed_runtime`
- **AND** the registered main command contains detailed stage prompts instead of a runtime-entry invocation
- **WHEN** generated runtime validation runs
- **THEN** validation MUST fail.
