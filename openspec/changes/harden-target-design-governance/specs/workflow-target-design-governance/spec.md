# workflow-target-design-governance Specification

## ADDED Requirements

### Requirement: Target design terminology is distinct from WorkflowProgram product design

WorkflowProgram SHALL distinguish its own product design documents from design-source artifacts generated for a target workflow.

#### Scenario: Documentation uses explicit target terminology

- **GIVEN** a generated target workflow design artifact is referenced in docs, prompts, templates, or reports
- **WHEN** the artifact is described
- **THEN** it uses `target design source`, `target design overview`, `target design detail`, or equivalent target-prefixed wording
- **AND** it does not use unqualified `HighLevel` or `LowLevel` that could be confused with WorkflowProgram product design

#### Scenario: Product design remains explicitly named

- **GIVEN** WorkflowProgram's own design documents are referenced
- **WHEN** docs or prompts mention those documents
- **THEN** they use `WP product design` or `WorkflowProgram product design` wording
- **AND** they do not imply those documents are generated target workflow artifacts

### Requirement: Target design source artifacts use canonical target-prefixed names

New target workflow develop runs SHALL emit canonical target-prefixed design-source artifact names and SHALL keep legacy names readable only for migration compatibility.

#### Scenario: New develop run emits canonical target design source

- **GIVEN** `workflowprogram-develop` creates or modifies a target workflow
- **WHEN** S1 through S3 design evidence is produced
- **THEN** the run evidence includes `outputs/stages/target-requirements.yaml`
- **AND** it includes `outputs/stages/target-context-findings.yaml`
- **AND** it includes `outputs/stages/target-design-overview.md`
- **AND** it includes `outputs/stages/target-design-detail.md`
- **AND** it includes `outputs/stages/target-implementation-plan.md`
- **AND** it includes `outputs/stages/target-acceptance-tests.yaml`
- **AND** it includes `outputs/stages/target-traceability-matrix.json`

#### Scenario: Legacy aliases are accepted during migration

- **GIVEN** a target workflow run has legacy design-source names such as `s3-design-highlevel.md` or `s3-design-lowlevel.md`
- **WHEN** validation runs during the migration period
- **THEN** WorkflowProgram may accept the legacy names
- **AND** it emits warnings recommending canonical target-prefixed names

### Requirement: Spec declares target design refs as a projection index

`workflow-spec.yaml.design_refs` SHALL declare the target design-source references and SHALL NOT embed full design prose.

#### Scenario: Complete target design refs pass validation

- **GIVEN** `workflow-spec.yaml.design_refs.schema_version` is `2`
- **AND** `design_refs.naming` is `target_design_v1`
- **AND** canonical refs exist for requirements, context findings, design overview, design detail, implementation plan, acceptance tests, and traceability matrix
- **WHEN** `validate-workflow-spec.py` validates the spec
- **THEN** the design refs validation passes

#### Scenario: Missing required canonical refs fail new target validation

- **GIVEN** a newly generated target workflow spec uses `design_refs.schema_version=2`
- **WHEN** `design_refs.design_overview`, `design_refs.design_detail`, or `design_refs.traceability_matrix` is missing
- **THEN** `validate-workflow-spec.py` fails the spec

#### Scenario: Unsafe design ref path fails validation

- **GIVEN** `workflow-spec.yaml.design_refs.design_detail` points outside `outputs/stages/**`
- **WHEN** spec validation runs
- **THEN** validation fails

#### Scenario: Persistent design refs use target design archive paths

- **GIVEN** `workflow-spec.yaml.design_refs.persistent` is declared
- **WHEN** spec validation runs
- **THEN** every persistent ref points under `.workflowprogram/design/source/**`
- **AND** unsafe or absolute persistent paths fail validation

### Requirement: Target design refs use one shared resolver

WorkflowProgram SHALL resolve canonical and legacy target design-source paths through a shared resolver instead of duplicating hardcoded path lists across scripts.

#### Scenario: Canonical refs resolve consistently

- **GIVEN** a spec declares `design_refs.schema_version=2` with canonical target-prefixed run refs and persistent refs
- **WHEN** spec validation, design-review packet generation, entry gating, runner artifact inference, S5, and publish eligibility inspect target design refs
- **THEN** each consumer resolves the same canonical artifact paths and kinds

#### Scenario: Legacy refs resolve through compatibility mode

- **GIVEN** a spec declares legacy fields such as `design_highlevel` and `design_lowlevel`
- **WHEN** validation or S5 runs during migration
- **THEN** the resolver returns legacy-compatible paths
- **AND** it records migration warnings

#### Scenario: Canonical design-review packet uses resolved refs

- **GIVEN** canonical target design source files exist
- **WHEN** `generate-design-review-packet.py` builds a review packet
- **THEN** the packet fingerprints the resolved canonical artifacts
- **AND** `validate-design-review-gate.py` validates those fingerprints without requiring legacy filenames

### Requirement: Completed target workflows persist design source archives

Completed develop runs SHALL persist target design source under the target workflow's managed `.workflowprogram/design/source/**` archive.

#### Scenario: Develop persists target design source

- **GIVEN** a develop run reaches managed apply
- **WHEN** candidate assets are staged
- **THEN** canonical target design source files are staged under `outputs/candidate/.workflowprogram/design/source/**`
- **AND** managed apply may write them because `.workflowprogram/design/**` is an allowed managed prefix

#### Scenario: Publish rejects missing persistent target design source

- **GIVEN** a target workflow declares target design governance
- **WHEN** `workflowprogram-publish` validates eligibility
- **THEN** publish eligibility requires persistent target design source files under `.workflowprogram/design/source/**`
- **AND** missing persistent design source blocks publish unless the run is explicitly accepted as a legacy compatibility case

### Requirement: Complex target graph nodes have detailed node design or explicit exemption

WorkflowProgram SHALL require dedicated target node-design evidence for complex target workflow nodes unless an explicit exemption is recorded.

#### Scenario: Complex node has node design

- **GIVEN** `workflow_graph.nodes[*].id` is `build_dfd`
- **AND** the node declares `complexity: complex` or `node_design_required: true`
- **AND** `design_refs.node_designs.build_dfd` points to `outputs/stages/target-node-designs/build_dfd.md`
- **WHEN** spec and S5 validation run
- **THEN** the node-design requirement passes

#### Scenario: Complex node missing node design fails

- **GIVEN** a workflow graph node declares `complexity: complex`
- **AND** the node has no matching `design_refs.node_designs` entry
- **AND** the node has no valid `node_design_exemption`
- **WHEN** S5 judges the run
- **THEN** S5 reports `FAIL`
- **AND** the failure kind is `design`

#### Scenario: Exempt complex node records accepted reason

- **GIVEN** a complex workflow graph node does not need a separate node-design file
- **WHEN** the spec omits the node-design reference
- **THEN** the node declares `node_design_exemption.reason`
- **AND** it declares `node_design_exemption.accepted_by`
- **AND** S5 records the exemption instead of failing the run

### Requirement: Target traceability matrix covers requirements, graph nodes, tests, assets, and evidence

WorkflowProgram SHALL validate that target workflow requirements are traceable through design, target graph, spec, target assets, acceptance tests, and runtime evidence.

#### Scenario: Requirement coverage is complete

- **GIVEN** `target-requirements.yaml` contains `REQ-001`
- **AND** `target-traceability-matrix.json` links `REQ-001` to at least one target design reference, workflow graph node or infrastructure exemption, acceptance test, and expected evidence path
- **WHEN** S5 validates design governance
- **THEN** requirement traceability passes

#### Scenario: Requirement is missing from traceability

- **GIVEN** `target-requirements.yaml` contains `REQ-001`
- **AND** `target-traceability-matrix.json` does not include `REQ-001`
- **WHEN** S5 validates design governance
- **THEN** S5 reports a target traceability failure

#### Scenario: Semantic target asset has no lineage

- **GIVEN** managed apply writes a semantic target asset such as a command, skill, agent, hook, or runtime behavior file
- **AND** the traceability matrix links that asset to no requirement, user feedback id, or resolved design-review issue
- **WHEN** S5 judges the run
- **THEN** S5 reports a target design governance failure

### Requirement: Target acceptance tests represent business behavior

WorkflowProgram SHALL keep business acceptance tests separate from runtime smoke `test_contract` and SHALL validate their linkage to requirements and evidence.

#### Scenario: Acceptance test links requirement and evidence

- **GIVEN** `target-acceptance-tests.yaml` defines `AT-001`
- **WHEN** the test is validated
- **THEN** it declares at least one `requirement_id`
- **AND** it declares expected outputs or expected evidence paths
- **AND** the traceability matrix links `AT-001` to its requirement

#### Scenario: Acceptance test without requirement fails

- **GIVEN** `target-acceptance-tests.yaml` contains a test with no requirement ids
- **WHEN** the target acceptance validator runs
- **THEN** validation fails

### Requirement: Modification runs update target design governance evidence

When an existing target workflow is modified, WorkflowProgram SHALL connect change-policy evidence to updated target design source, spec, acceptance tests, and traceability.

#### Scenario: Semantic modification updates design source or justifies no update

- **GIVEN** a change policy permits modifying a semantic target asset
- **WHEN** the run changes a command, skill, agent, workflow graph, runtime behavior, or test behavior
- **THEN** the run updates target design source and traceability
- **OR** `impact-analysis.json` explicitly justifies why no design-source or acceptance-test update is required

#### Scenario: Semantic modification bypasses traceability

- **GIVEN** managed apply writes a semantic target asset
- **AND** no target design source, target acceptance test, traceability matrix, or valid impact-analysis justification covers the change
- **WHEN** S5 validates the run
- **THEN** S5 reports `FAIL`
- **AND** the failure kind is `design`
