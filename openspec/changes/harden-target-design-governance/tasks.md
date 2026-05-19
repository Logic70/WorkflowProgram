# Tasks

## 1. OpenSpec And Active Design Truth

- [x] 1.1 Record the terminology split: `WP product design`, `target design source`, `target runtime map`, and `target derived views`.
- [x] 1.2 Update WorkflowProgram product high-level/low-level docs to avoid unqualified `HighLevel` / `LowLevel` when referring to target workflows.
- [x] 1.3 Document canonical target design source names and legacy aliases.
- [x] 1.4 Document that target workflows remain free to use request-specific `workflow_graph` nodes and are not forced into `S1..S6`.

## 2. Prompt, Skill, And Template Updates

- [x] 2.1 Update `workflowprogram-develop` so new runs emit canonical target design source names.
- [x] 2.2 Update `workflow-spec-support/spec-template.md` to request target design overview/detail, target acceptance tests, and target traceability matrix.
- [x] 2.3 Update `workflow-spec-support/yaml-spec-template.md` so `design_refs` uses `schema_version: 2`, `naming: target_design_v1`, canonical target-prefixed run paths, and `.workflowprogram/design/source/**` persistent paths.
- [x] 2.4 Update generated view/lowlevel language so `workflow-view.md` and `workflow-lowlevel.md` are clearly described as derived target views, not target design source.

## 3. Shared Resolver And Spec Validator

- [x] 3.1 Add shared `lib/target_design_refs.py` resolver for canonical run refs, persistent target refs, legacy aliases, node-design paths, artifact kinds, and migration warnings.
- [x] 3.2 Add resolver unit tests for canonical, legacy, mixed, unsafe, missing, and persistent-path cases.
- [x] 3.3 Extend `validate-workflow-spec.py` to support `design_refs.schema_version`, `design_refs.naming`, `design_overview`, `design_detail`, and `design_refs.persistent`.
- [x] 3.4 Keep legacy aliases `design_highlevel` and `design_lowlevel` readable with warnings during migration.
- [x] 3.5 Require complete canonical `design_refs` for newly generated target workflows.
- [x] 3.6 Add workflow graph node metadata validation for `complexity`, `design_intensity`, `node_design_required`, and `node_design_exemption`.
- [x] 3.7 Validate `design_refs.node_designs` paths under `outputs/stages/target-node-designs/**`, while accepting legacy `outputs/stages/node-designs/**` with warnings.
- [x] 3.8 Validate `design_refs.persistent.*` paths under `.workflowprogram/design/source/**`.
- [x] 3.9 Add spec fixtures for canonical valid, legacy alias warning, missing required design refs, complex node missing design, complex node exemption, and invalid persistent path.

## 4. Target Design Artifact Validators

- [x] 4.1 Add or extend a validator for `target-requirements.yaml`.
- [x] 4.2 Add or extend a validator for `target-acceptance-tests.yaml`.
- [x] 4.3 Add or extend a validator for `target-traceability-matrix.json`.
- [x] 4.4 Validate every requirement has traceability to design, workflow graph node or infrastructure exemption, acceptance test, and evidence.
- [x] 4.5 Validate every acceptance test links to at least one requirement and expected evidence path.
- [x] 4.6 Validate every complex target node has a node design or a valid exemption.

## 5. Runtime And Gate Integration

- [x] 5.1 Update `generate-design-review-packet.py` to resolve canonical refs from `workflow-spec.yaml`, fallback to canonical defaults, then fallback to legacy aliases.
- [x] 5.2 Keep `validate-design-review-gate.py` fingerprint-based and add tests proving canonical fingerprint staleness is detected.
- [x] 5.3 Update `workflow-entry.py` design-review-required detection to use the resolver instead of legacy marker paths.
- [x] 5.4 Update `workflow-entry.py` to stage `outputs/candidate/.workflowprogram/design/source/**` from canonical target design source before managed apply.
- [x] 5.5 Update `workflow-runner.py` artifact-kind inference for canonical target design source paths.
- [x] 5.6 Update `validate-run-state.py` only if new artifact kinds are needed; otherwise keep existing kinds and map canonical paths to them.

## 6. S5 Judge Integration

- [x] 6.1 Update `workflow-s5-judge.py` to use the shared resolver for design refs, node designs, traceability, and acceptance tests.
- [x] 6.2 Add S5 checks for complete target design refs and artifact existence.
- [x] 6.3 Add S5 checks for requirement coverage in `target-traceability-matrix.json`.
- [x] 6.4 Add S5 checks for workflow graph node coverage in traceability.
- [x] 6.5 Add S5 checks for target acceptance test coverage.
- [x] 6.6 Add S5 checks for complex node design coverage or exemption.
- [x] 6.7 Add S5 checks that modification runs update target design source or provide a valid impact-analysis explanation.
- [x] 6.8 Update S5 semantic-change checks to use the resolver's active traceability path instead of hardcoded `traceability-matrix.json`.

## 7. Runtime Providers, Publish, And Fixtures

- [x] 7.1 Update deterministic fixture host to emit canonical target design source artifacts for develop runs.
- [x] 7.2 Update command adapter mock paths to use canonical target design names.
- [x] 7.3 Preserve legacy fixture coverage to prove migration compatibility.
- [x] 7.4 Update `validate-publish-eligibility.py` to require persistent target design source for target-design-governed workflows.
- [x] 7.5 Add a smoke fixture where canonical target design governance passes and persistent `.workflowprogram/design/source/**` exists after managed apply.
- [x] 7.6 Add a smoke fixture where missing target design refs fail.
- [x] 7.7 Add a smoke fixture where missing persistent target design source fails publish eligibility.
- [x] 7.8 Add a smoke fixture where a complex node missing node design fails.
- [x] 7.9 Add a smoke fixture where a modification changes semantic assets without traceability and fails.
- [x] 7.10 Add a smoke fixture where impact analysis justifies no acceptance-test update and S5 records the rationale.

## 8. Documentation

- [x] 8.1 Update README and plugin README with the distinction between WorkflowProgram product design and target workflow design.
- [x] 8.2 Update user-facing docs to explain canonical target design artifacts and when node-design files are required.
- [x] 8.3 Update publish docs to state publish consumes target design governance evidence but does not create or repair it.
- [x] 8.4 Update active WP product high-level/low-level/status/consistency docs to name target design source separately from WP product design.

## 9. Verification

- [x] 9.1 Run `openspec validate harden-target-design-governance --strict`.
- [x] 9.2 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 9.3 Run spec validator fixtures.
- [x] 9.4 Run target design artifact validator tests.
- [x] 9.5 Run design-review gate unit tests.
- [x] 9.6 Run publish eligibility fixtures.
- [x] 9.7 Run relevant runtime smoke fixtures.
- [x] 9.8 Run `python3 tools/runtime_smoke_matrix.py`.
