# Design

## 1. Terminology

Use explicit names for the two design layers:

| Layer | New term | Current examples | Meaning |
| --- | --- | --- | --- |
| WorkflowProgram product design | `WP product design` | `docs/workflowprogram-stage-highlevel-design.md`, `docs/workflowprogram-stage-lowlevel-design.md` | Design of WorkflowProgram itself. |
| Generated workflow design source | `target design source` | `outputs/stages/s3-design-highlevel.md`, `outputs/stages/s3-design-lowlevel.md` | Human-reviewable design for the workflow being created or modified. |
| Generated workflow machine projection | `target runtime map` | `TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml` | Machine-readable map used by validators, runtime, and S5. |
| Generated workflow derived reports | `target derived views` | `workflow-view.md`, `workflow-maintenance.md` | Generated from YAML; cannot introduce new semantics. |

The words `HighLevel` and `LowLevel` should not be used without a qualifier. Product docs may use `WP product high-level design`; target artifacts should use `target design overview` and `target design detail`.

## 2. Canonical Target Design Source Set

New target workflows SHALL use target-prefixed artifact names:

| Canonical artifact | Legacy alias | Responsibility |
| --- | --- | --- |
| `outputs/stages/target-requirements.yaml` | `outputs/stages/s1-requirements.yaml` | Requirement IDs, user goal, success criteria, boundaries, acceptance hints. |
| `outputs/stages/target-question-backlog.json` | `outputs/stages/open-questions.json` | Blocking and non-blocking unresolved questions. |
| `outputs/stages/target-requirement-logic-map.json` | `outputs/stages/requirement-logic-map.json` | Seven-logic-lens decomposition and coverage. |
| `outputs/stages/target-context-findings.yaml` | `outputs/stages/s2-context-findings.yaml` | Repository/domain/context findings linked to requirement IDs. |
| `outputs/stages/target-design-overview.md` | `outputs/stages/s3-design-highlevel.md` | Target workflow purpose, actors, major business nodes, boundaries, and enabled capabilities. |
| `outputs/stages/target-design-detail.md` | `outputs/stages/s3-design-lowlevel.md` | Node behavior, prompts, tool usage, inputs, outputs, failure paths, and validation rules. |
| `outputs/stages/target-implementation-plan.md` | `outputs/stages/s3-implementation-plan.md` | Implementation tasks derived from accepted target design. |
| `outputs/stages/target-acceptance-tests.yaml` | `outputs/stages/acceptance-tests.yaml` | Business acceptance tests linked to requirement IDs. |
| `outputs/stages/target-traceability-matrix.json` | `outputs/stages/traceability-matrix.json` | Links requirements to target design nodes, spec sections, assets, tests, and evidence. |
| `outputs/stages/target-node-designs/<node-id>.md` | `outputs/stages/node-designs/<node-id>.md` | Detailed design for complex target workflow nodes. |

Legacy aliases remain supported as read-compatible inputs during migration. New generated runs should emit canonical names and may optionally duplicate or reference legacy names only for compatibility.

## 3. Target Design Contract In `workflow-spec.yaml`

`workflow-spec.yaml` remains the target runtime map. It SHOULD NOT embed full design prose. It SHALL declare where target design source artifacts live and what lineage policy applies.

Extend `design_refs` rather than adding a competing top-level design document:

```yaml
design_refs:
  schema_version: 2
  naming: target_design_v1
  # Run evidence refs are relative to RUN_ROOT and are used by the develop-run S5 judge.
  requirements: outputs/stages/target-requirements.yaml
  question_backlog: outputs/stages/target-question-backlog.json
  requirement_logic_map: outputs/stages/target-requirement-logic-map.json
  context_findings: outputs/stages/target-context-findings.yaml
  design_overview: outputs/stages/target-design-overview.md
  design_detail: outputs/stages/target-design-detail.md
  implementation_plan: outputs/stages/target-implementation-plan.md
  acceptance_tests: outputs/stages/target-acceptance-tests.yaml
  traceability_matrix: outputs/stages/target-traceability-matrix.json
  node_designs:
    build_dfd: outputs/stages/target-node-designs/build_dfd.md
  node_design_policy:
    required_for_complex_nodes: true
    exemption_field: node_design_exemption
  # Persistent refs are relative to TARGET_ROOT and make the completed target workflow self-describing.
  persistent:
    requirements: .workflowprogram/design/source/target-requirements.yaml
    context_findings: .workflowprogram/design/source/target-context-findings.yaml
    design_overview: .workflowprogram/design/source/target-design-overview.md
    design_detail: .workflowprogram/design/source/target-design-detail.md
    implementation_plan: .workflowprogram/design/source/target-implementation-plan.md
    acceptance_tests: .workflowprogram/design/source/target-acceptance-tests.yaml
    traceability_matrix: .workflowprogram/design/source/target-traceability-matrix.json
    node_designs:
      build_dfd: .workflowprogram/design/source/target-node-designs/build_dfd.md
```

Required for newly generated target workflows:

- `schema_version`
- `naming`
- `requirements`
- `context_findings`
- `design_overview`
- `design_detail`
- `implementation_plan`
- `acceptance_tests`
- `traceability_matrix`

Recommended but conditionally required:

- `question_backlog` when S1 carried open non-blocking questions.
- `requirement_logic_map` when the seven-lens clarification subsystem ran.
- `node_designs` for complex target nodes.

Persistent refs are required for completed develop runs that apply managed assets. They are not used as the primary S5 evidence for the current run; they exist so later modification, audit, validate, and publish flows can read the target workflow's own design source without depending on an old `RUN_ROOT`.

## 3.1 Shared Target Design Reference Resolver

Current implementation has legacy design-source names hardcoded in multiple places. This change must not create a second set of divergent path rules. Add a shared resolver, for example `lib/target_design_refs.py`, and make all consumers use it.

Responsibilities:

- normalize canonical `design_refs.schema_version=2` fields;
- read legacy aliases such as `design_highlevel`, `design_lowlevel`, `s3-design-highlevel.md`, and `node-designs/**`;
- expose canonical run refs, legacy fallback refs, and persistent target refs;
- classify each ref by artifact kind;
- resolve node-design refs for canonical `target-node-designs/**` and legacy `node-designs/**`;
- report migration warnings in one place.

Consumers that must use the resolver:

- `validate-workflow-spec.py`;
- `workflow-s5-judge.py`;
- `workflow-entry.py` design-review gate trigger;
- `generate-design-review-packet.py`;
- `workflow-runner.py` artifact-kind inference;
- `runtime_host.py` and `tools/mock_runtime_host.py`;
- `validate-publish-eligibility.py`;
- workflow spec templates and deterministic tests.

## 4. Complex Target Node Rule

`workflow_graph.nodes[*]` SHALL support optional metadata:

```yaml
workflow_graph:
  nodes:
    - id: build_dfd
      template: stride_dfd
      role: derive DFD from code
      complexity: complex
      design_intensity: detailed
      node_design_required: true
      input_refs: [...]
      output_refs: [...]
```

A node requires a target node-design file when any of these is true:

- `node_design_required: true`
- `complexity: complex`
- `design_intensity: detailed`
- `loop_policy.enabled: true`
- the node consumes or produces security-, reverse-engineering-, or safety-critical evidence;
- the node uses multiple host capabilities, external binaries, MCP servers, or specialized agents;
- the node has non-trivial branching, TDD loops, or failure recovery.

If a node meets the rule but intentionally has no node design, it must declare:

```yaml
node_design_exemption:
  reason: "..."
  accepted_by: "user | design_review"
```

S5 treats missing node design without an exemption as `FAIL/design`.

## 5. Traceability Contract

`target-traceability-matrix.json` SHALL be machine-readable and include entries shaped like:

```json
{
  "schema_version": 1,
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "design_refs": ["target-design-overview.md#goal"],
      "workflow_graph_nodes": ["build_dfd"],
      "spec_paths": ["workflow_graph.nodes[build_dfd]", "test_contract.artifacts.deliverables"],
      "target_assets": [".claude/skills/stride/SKILL.md"],
      "acceptance_tests": ["AT-001"],
      "runtime_evidence": ["outputs/stages/team-results.json", "state.json"]
    }
  ]
}
```

Validation rules:

- Every requirement ID in `target-requirements.yaml` must appear in the traceability matrix.
- Every workflow graph node must be linked to at least one requirement or marked as infrastructure-only.
- Every acceptance test must link to at least one requirement and one expected evidence path.
- Every semantic target asset must link to at least one requirement or design-review resolution.
- Modification runs must link changed artifacts to either original requirements or user feedback/change-policy IDs.

## 6. Acceptance Test Contract

`target-acceptance-tests.yaml` SHALL complement, not replace, `test_contract`.

- `test_contract` remains the runtime smoke and artifact contract.
- `target-acceptance-tests.yaml` defines business-level behavior that the target workflow must satisfy.

Minimum test case fields:

```yaml
schema_version: 1
tests:
  - id: AT-001
    requirement_ids: [REQ-001]
    workflow_graph_nodes: [build_dfd]
    setup: "Repository fixture with entrypoints and network boundaries"
    action: "Run DFD generation node"
    expected_outputs:
      - outputs/dfd.md
    expected_evidence:
      - state.json
    pass_criteria:
      - "DFD lists external actors, processes, data stores, and trust boundaries"
```

S5 checks the file structurally. Domain correctness remains model-reviewed by the design-review gate and runtime evidence review.

## 7. Modification Flow Governance

For existing target workflows, change-policy evidence must connect to the same target design source set:

```text
user feedback
  -> change-context.json
  -> change-policy.json
  -> impact-analysis.json
  -> updated target design source
  -> updated workflow-spec.yaml
  -> updated target acceptance tests
  -> updated traceability matrix
  -> managed apply
  -> S5 evidence
```

Rules:

- Semantic changes must update `target-design-overview.md` or `target-design-detail.md` before generated assets change.
- `workflow-spec.yaml` must project the updated design decision.
- If a change affects business behavior, `target-acceptance-tests.yaml` and `target-traceability-matrix.json` must change or the impact analysis must explain why not.
- S5 must reject managed semantic writes that are not traceable to a requirement, user feedback ID, or resolved design-review issue.

## 8. Validator And Runtime Responsibilities

### `validate-workflow-spec.py`

Add strict validation for `design_refs.schema_version=2`:

- require canonical fields for new target workflows;
- accept legacy aliases with warnings;
- validate safe `outputs/stages/**` paths;
- validate `target-node-designs/**` paths;
- validate `design_refs.persistent.*` paths under `.workflowprogram/design/source/**`;
- validate complex-node metadata and exemption schema;
- reject unknown `design_refs` fields in strict mode.

### `workflow-s5-judge.py`

Add target design governance checks:

- `target_design_refs_complete`
- `target_design_artifacts_exist`
- `target_traceability_covers_requirements`
- `target_traceability_covers_graph_nodes`
- `target_acceptance_tests_cover_requirements`
- `target_complex_nodes_have_design_or_exemption`
- `target_change_policy_updates_design_source`

### Generators and templates

- `workflowprogram-develop` should produce canonical target design source names.
- `workflow-spec-support` templates should use target-prefixed names.
- `generate-workflow-view.py` and `generate-workflow-maintenance.py` should label outputs as derived target views and include the target design contract summary.
- `workflow-entry.py` should stage the canonical target design source archive under `outputs/candidate/.workflowprogram/design/source/**` before managed apply.
- `managed-assets.py` already allows `.workflowprogram/design/**`, so no new write prefix is required.

### Design review gate

The S3 design-review gate currently reads fixed legacy artifact names. It must be updated to use the shared resolver:

- packet generation records canonical names when present;
- legacy names are accepted during migration and recorded as aliases;
- packet fingerprints are attached to resolved artifact paths, not hardcoded legacy paths;
- gate validation remains fingerprint-based and does not need to know the naming style.

### Publish eligibility

Publish eligibility should require persistent target design source for target-design-governed workflows:

- `TARGET_ROOT/.workflowprogram/design/source/target-design-overview.md`;
- `TARGET_ROOT/.workflowprogram/design/source/target-design-detail.md`;
- `TARGET_ROOT/.workflowprogram/design/source/target-acceptance-tests.yaml`;
- `TARGET_ROOT/.workflowprogram/design/source/target-traceability-matrix.json`.

During migration, publish may accept legacy completed workflows only when the latest develop `RUN_ROOT` still contains valid legacy design evidence and the publish report records the compatibility mode.

## 9. Migration Strategy

The first implementation should avoid breaking existing target workflows abruptly:

- Keep reading legacy `design_refs.design_highlevel` and `design_refs.design_lowlevel`.
- Emit warnings recommending `design_overview` and `design_detail`.
- New generated workflows use canonical names.
- New completed develop runs persist target design source under `.workflowprogram/design/source/**`.
- Add a repository validator marker so WorkflowProgram's own templates and fixtures must use canonical names.
- After migration fixtures pass, a later change may promote legacy aliases from warning to error.

## 10. Closure Review

### Round 1

Finding:

- The first draft risked adding a new top-level design document inside `workflow-spec.yaml`, which would conflict with the existing decision that YAML is a runtime map.

Decision: accept.

Fix:

- Extend `design_refs` as a projection index and policy declaration only.
- Keep full target design prose in external target design source files.

Verification:

- `validate-workflow-spec.py` tasks only validate refs, schema, and policies; they do not parse long design prose into YAML.

### Round 2

Finding:

- Renaming artifacts could break existing S5 checks and fixtures that look for `s3-design-highlevel.md`, `s3-design-lowlevel.md`, and `traceability-matrix.json`.

Decision: accept.

Fix:

- Define canonical target-prefixed names plus legacy aliases.
- Require new generated runs to use canonical names while validators temporarily accept legacy aliases with warnings.

Verification:

- Add valid canonical fixtures and legacy-alias fixtures.
- Add S5 checks that resolve either canonical or legacy paths during migration.

### Round 3

Finding:

- Requiring node-design files for every workflow graph node would make simple workflows too heavy.

Decision: accept.

Fix:

- Require node design only for complex nodes by explicit metadata or deterministic triggers.
- Allow explicit node-design exemption with reason and reviewer/user acceptance.

Verification:

- Add fixtures for simple node without node design, complex node with node design, and complex node missing design.

### Round 4

Finding:

- Acceptance-test requirements could duplicate existing `test_contract`.

Decision: accept.

Fix:

- Define `test_contract` as runtime smoke/artifact contract.
- Define `target-acceptance-tests.yaml` as business behavior contract linked to requirements and evidence.

Verification:

- Add S5 checks that verify linkage, not duplicate runtime execution semantics.

### Round 5

Finding:

- The change-policy connection could drift into a second implementation of controlled evolution.

Decision: accept.

Fix:

- Reuse existing `change-policy.json`, `impact-analysis.json`, and design-review gate.
- Add only traceability checks that modified semantic artifacts have updated design source or explicit impact-analysis explanation.

Verification:

- Add modification smoke fixture where changed assets without target design/traceability updates fail S5.

### Round 6: Existing Implementation Compatibility

Finding:

- Existing implementation hardcodes legacy names in `workflowprogram-develop`, `yaml-spec-template.md`, `spec-template.md`, `validate-workflow-spec.py`, `workflow-s5-judge.py`, `workflow-entry.py`, `workflow-runner.py`, `generate-design-review-packet.py`, `runtime_host.py`, `tools/mock_runtime_host.py`, and tests.
- Directly switching to target-prefixed names would break design-review gate, S5 lineage checks, runner artifact inference, and deterministic smoke fixtures.

Decision: accept.

Fix:

- Add the shared target design reference resolver as a required implementation step.
- Canonical names are used for new outputs, while legacy names remain readable through the resolver during migration.
- All consumers listed in Section 3.1 must use the resolver instead of open-coded path lists.

Verification:

- Add resolver unit tests for canonical, legacy, mixed, unsafe, and missing refs.
- Add smoke coverage proving canonical runs pass and legacy fixtures still pass with warnings.

### Round 7: Persistent Target Design Source

Finding:

- `workflow-spec.yaml` is persisted to `TARGET_ROOT/.workflowprogram/design/`, but current `design_refs` point to `RUN_ROOT/outputs/stages/**`.
- That is sufficient for the current run's S5 evidence but insufficient for later modification, validate, audit, or publish flows that need the completed target workflow's own design source.

Decision: accept.

Fix:

- Extend `design_refs` with a `persistent` mapping under `.workflowprogram/design/source/**`.
- Stage target design source archive assets into `outputs/candidate/.workflowprogram/design/source/**` during develop.
- Publish eligibility checks persistent design source for target-design-governed workflows.

Verification:

- Add a develop smoke fixture that inspects `TARGET_ROOT/.workflowprogram/design/source/**` after managed apply.
- Add a publish eligibility fixture that fails when persistent target design source is missing.

### Round 8: Design Review Gate Fingerprint Compatibility

Finding:

- `generate-design-review-packet.py` currently fingerprints fixed legacy paths. Canonical files would make the packet fail even if the design source is complete.

Decision: accept.

Fix:

- Packet generation resolves design refs from `workflow-spec.yaml` when available.
- If no spec refs exist yet, it falls back to canonical default paths, then legacy paths.
- `validate-design-review-gate.py` remains path-agnostic and validates the fingerprints recorded in the packet.

Verification:

- Add unit tests for canonical packet generation, legacy fallback, and stale canonical artifact detection.

### Round 9: Change Policy And Traceability Alignment

Finding:

- Current change-policy and S5 checks refer to `traceability-matrix.json` and legacy S3 design paths. The new design could cause semantic modifications to pass without updating canonical target governance files if checks are not redirected.

Decision: accept.

Fix:

- S5 semantic-change checks use the resolver's active traceability path.
- Modification conformance requires either changed canonical target governance artifacts or a valid impact-analysis explanation.
- Legacy change-policy fixtures are preserved but compatibility mode is reported.

Verification:

- Add a modification fixture where `.claude/**` changes while canonical traceability is stale; S5 must fail.
- Add a fixture where impact analysis justifies no acceptance-test update; S5 may pass with recorded rationale.

### Round 10: Final Closure Review

Finding:

- No new actionable incompatibility was found after adding the resolver, persistent design archive, design-review packet migration, S5 resolver usage, and publish eligibility updates.

Decision: accept.

Fix:

- No further design changes.

Verification:

- `openspec validate harden-target-design-governance --strict` must remain green.

Latest review round found no new actionable issues.
