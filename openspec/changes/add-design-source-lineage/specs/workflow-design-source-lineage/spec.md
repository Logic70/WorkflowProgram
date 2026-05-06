# workflow-design-source-lineage Specification

## ADDED Requirements

### Requirement: Design source stays separate from machine projection

WorkflowProgram SHALL keep high-level/low-level design reasoning in explicit design-source artifacts and SHALL use `workflow-spec.yaml` primarily as a runtime/control-plane projection.

#### Scenario: YAML references design source

- **GIVEN** S3 has produced design-source artifacts
- **WHEN** `workflow-spec.yaml` is finalized
- **THEN** it MAY include `design_refs` pointing to those artifacts
- **AND** it SHOULD NOT embed full design prose as replacement for those artifacts.

### Requirement: S1 produces traceable requirements

S1 SHALL produce a structured requirement index that preserves the raw user need, clarified intent, acceptance hints, and boundaries.

#### Scenario: Requirement index exists

- **GIVEN** a develop run reaches S1 successfully
- **WHEN** runtime evidence is inspected
- **THEN** `outputs/stages/s1-requirements.yaml` SHOULD exist
- **AND** each requirement SHOULD have a stable id usable by downstream artifacts.

### Requirement: S2 findings link back to requirements

S2 context findings SHALL be linkable to requirement ids so research and repository context do not become detached from the user goal.

#### Scenario: Context finding references a requirement

- **GIVEN** S2 records a context finding
- **WHEN** the finding is consumed by S3
- **THEN** it SHOULD include one or more requirement references where applicable.

### Requirement: S3 emits reviewable design source and implementation plan

S3 SHALL produce reviewable high-level design, low-level design, implementation plan, acceptance tests, and traceability matrix before S4 asset generation.

#### Scenario: Complex design is accepted

- **GIVEN** a target workflow has non-trivial domain logic
- **WHEN** S3 is approved
- **THEN** downstream generation has design source, acceptance tests, and traceability data to follow.

### Requirement: `design_refs` uses safe relative paths

`workflow-spec.yaml.design_refs` MAY reference design-source artifacts and MUST only use safe relative paths under `outputs/stages/`. `node_designs` entries MUST live under `outputs/stages/node-designs/`.

#### Scenario: Design ref escapes run root

- **GIVEN** a spec declares `design_refs.design_lowlevel: ../secret.md`
- **WHEN** spec validation runs
- **THEN** validation MUST fail.

### Requirement: Complex target nodes use node design instead of nested S1-S6

Complex target workflow nodes MAY use dedicated node-design files, but MUST NOT imply a second WorkflowProgram S1-S6 lifecycle inside the target workflow.

#### Scenario: STRIDE DFD node needs detail

- **GIVEN** a STRIDE workflow contains a complex `build_dfd` node
- **WHEN** the node needs repository reading, data-flow extraction, and trust-boundary reasoning
- **THEN** the workflow MAY declare `design_refs.node_designs.build_dfd`
- **AND** WorkflowProgram's product lifecycle remains unchanged.

### Requirement: Nodes and agents are not one-to-one by default

A target workflow node SHALL NOT require an independent agent unless the design justifies specialized expertise, context isolation, parallel review, or ownership separation.

#### Scenario: Simple sequential flow

- **GIVEN** a target workflow has three simple nodes
- **WHEN** there is no specialized capability or context boundary
- **THEN** those nodes MAY share one skill/agent implementation.

### Requirement: S5 verifies declared design lineage

When `design_refs` are declared, S5 SHALL verify the referenced files exist, node-design ids reference declared graph nodes, and requirement ids appear in the traceability matrix.

#### Scenario: Traceability matrix omits a requirement

- **GIVEN** `s1-requirements.yaml` contains `REQ-001`
- **AND** `traceability-matrix.json` does not reference `REQ-001`
- **WHEN** S5 validates the run
- **THEN** S5 MUST report a lineage failure.
