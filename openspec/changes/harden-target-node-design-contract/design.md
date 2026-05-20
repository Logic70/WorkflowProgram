# Design

## Decision Frame

User goal: feed FreeSTRIDE's practical `node_design` pattern back into WorkflowProgram so generated target workflows can carry reliable per-node design for complex nodes.

Scope boundary: this change strengthens target workflow design governance only. It does not redesign WorkflowProgram's S0..S6 control plane, add new runtime stages, or make all target nodes require separate design files.

Current truth to preserve:

- `workflow-spec.yaml.design_refs.node_designs` already indexes node-design files.
- `workflow_graph.nodes[*]` already owns node id, owner, template, input refs, output refs, gate, and optional loop policy.
- `validate-target-design-governance.py` and `workflow-s5-judge.py` already enforce node-design existence for complex nodes.
- Canonical node-design run evidence lives under `outputs/stages/target-node-designs/**`.

Output artifacts being changed:

- OpenSpec requirement and task plan.
- Node design template.
- Deterministic node-design validator.
- S5 and governance integration.
- Docs, prompts, fixtures, and tests.

## Target Node Design Contract

A target node design is the executable design contract for one target workflow node. It sits below target design overview/detail and above generated implementation assets.

It MUST answer these questions for the specific node:

- What is this node responsible for, and what is explicitly outside scope?
- Which upstream artifacts, user inputs, or runtime evidence does it consume?
- Which outputs does it produce, and who consumes them?
- Which agent, skill, script, CLI, MCP, or host capability performs the work?
- Which state/context fields are read or written?
- Which gate, loop, retry, failure, downgrade, and approval rules apply?
- Which tests, verifier checks, and runtime evidence prove the node worked?

`workflow-spec.yaml` keeps only the projection:

```yaml
design_refs:
  node_designs:
    build_dfd: outputs/stages/target-node-designs/build_dfd.md
```

The Markdown file carries the detailed prose and tables.

## Required Sections

New target node-design files SHALL follow the shared template and include these sections:

1. Node Metadata
2. Purpose And Boundary
3. Input Contract
4. Output Contract And Consumers
5. Context Read/Write Rules
6. Internal Execution Plan
7. Agent / Skill / Script / Tool Calls
8. Data Field Contract
9. Exit Gate
10. Failure, Retry, And Degrade Strategy
11. Verification And Tests
12. Observability And Debug Artifacts
13. Safety And Execution Constraints
14. Open Tasks And Extension Points

The validator checks heading presence and core projection consistency. It does not judge domain correctness; design review remains responsible for semantic quality.

## Projection Consistency Rules

`validate-target-node-design.py` validates a node design against `workflow-spec.yaml`:

- node id must match an existing `workflow_graph.nodes[*].id`;
- the document must reference `workflow_graph.nodes[id=<node-id>]`;
- declared owner, template, and gate must match the graph node when those fields exist;
- every `input_refs[]` entry from the graph node must appear in the node design;
- every `output_refs[]` entry from the graph node must appear in the node design;
- loop-enabled nodes must state that loop execution is allowed and must not claim loops are disallowed;
- failure strategy must include explicit failure/degrade semantics such as `FAIL`, `WARN`, `BLOCKED`, `ENVIRONMENT-SKIP`, or degrade wording;
- verification must include tests, verifier evidence, acceptance criteria, or runtime evidence;
- unresolved placeholders such as `TBD`, `TODO`, `待补`, `待确认`, or `REPLACE_ME` fail validation.

## Governance Integration

`validate-target-design-governance.py` remains the aggregate target design governance validator. It calls the node-design validator for each existing `design_refs.node_designs` entry.

S5 judge adds a deterministic check for each node design:

```text
target_node_design_<node-id>_content_valid
```

For canonical target design governance, invalid node-design content is a `FAIL/design`. Missing node-design coverage for required nodes remains handled by the existing complex-node rule.

## Template Placement

The canonical template lives at:

```text
.claude/skills/workflow-spec-support/target-node-design-template.md
```

It is prompt-facing support material. Runtime validation is owned by `validate-target-node-design.py`, not by the template itself.

## Compatibility

Legacy `outputs/stages/node-designs/**` references remain readable via the existing resolver, but the same content validation applies when a legacy file is present. This avoids treating legacy paths as a loophole.

## Closure Review

Round 1:

- Finding: The first draft risked turning every node into mandatory heavyweight documentation.
- Decision: accept.
- Fix: keep mandatory node design limited to already-defined triggers: complex nodes, detailed nodes, explicit `node_design_required`, loop-enabled nodes, and other high-risk/tool-heavy cases named in guidance.
- Verification: simple nodes in existing fixtures do not need node-design files.

Round 2:

- Finding: The node-design validator could duplicate graph schema validation.
- Decision: accept.
- Fix: validator only checks Markdown projection consistency against already-parsed graph node fields; schema correctness remains in `validate-workflow-spec.py`.
- Verification: implementation plan wires the validator after spec validation.

Round 3:

- Finding: FreeSTRIDE-specific STRIDE wording could leak into generic WorkflowProgram templates.
- Decision: accept.
- Fix: template uses generic node contract language; STRIDE remains an example domain, not a required schema.
- Verification: required sections contain no STRIDE-only fields.

Round 4:

- Finding: S5 could fail early on missing files before governance writes its own aggregate report.
- Decision: accept.
- Fix: S5 consumes node-design validation as an artifact check while aggregate governance still writes `target-design-governance-validation.json`.
- Verification: both checks can coexist and report the same failure with different granularity.
