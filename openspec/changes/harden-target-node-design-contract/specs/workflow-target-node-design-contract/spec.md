# workflow-target-node-design-contract Specification

## ADDED Requirements

### Requirement: Complex target nodes have content-validated node design

WorkflowProgram SHALL validate the content of target node-design files for complex or explicitly node-design-required target workflow nodes.

#### Scenario: Valid node design passes

- **GIVEN** `workflow_graph.nodes[*].id` is `build_dfd`
- **AND** `design_refs.node_designs.build_dfd` points to `outputs/stages/target-node-designs/build_dfd.md`
- **AND** the node-design file contains all required sections
- **AND** it matches the graph node id, owner, template, gate, input refs, and output refs
- **WHEN** target design governance validation runs
- **THEN** the node-design content validation passes

#### Scenario: Missing node-design section fails

- **GIVEN** a node-design file omits a required section such as `Verification And Tests`
- **WHEN** `validate-target-node-design.py` validates the file
- **THEN** validation fails

#### Scenario: Node-design projection mismatch fails

- **GIVEN** `workflow_graph.nodes[build_dfd].owner` is `dfd-builder`
- **AND** `outputs/stages/target-node-designs/build_dfd.md` declares a different owner
- **WHEN** node-design validation runs
- **THEN** validation fails

#### Scenario: Loop-enabled node-design must acknowledge loop execution

- **GIVEN** `workflow_graph.nodes[reverse_analysis].loop_policy.enabled` is `true`
- **WHEN** its node-design claims loops are disallowed or omits loop execution evidence
- **THEN** validation fails

### Requirement: S5 records node-design content validation evidence

S5 SHALL include deterministic checks for existing target node-design files.

#### Scenario: S5 records per-node node-design result

- **GIVEN** a target workflow spec declares `design_refs.node_designs.build_dfd`
- **WHEN** S5 judges the run
- **THEN** the check matrix includes `target_node_design_build_dfd_content_valid`
- **AND** the check status reflects `validate-target-node-design.py`

#### Scenario: Invalid node design is design failure

- **GIVEN** a required target node-design file exists but fails content validation
- **WHEN** S5 computes the final verdict
- **THEN** S5 reports `FAIL`
- **AND** the failure kind is `design`
