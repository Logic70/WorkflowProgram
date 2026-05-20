# Tasks

## 1. Design Contract

- [x] 1.1 Document the two-layer model: WorkflowProgram lifecycle `S0..S6` vs target workflow `workflow_graph`.
- [x] 1.2 Update HighLevel and LowLevel docs to state that generated target workflows do not need to follow the S1-S6 template.
- [x] 1.3 Define `workflow-spec.md` as accepted human readback and `workflow-spec.yaml` as the only machine-readable semantic source.
- [x] 1.4 Mark `workflow-view.md` and `workflow-maintenance.md` as derived non-semantic reports for target graph decisions.

## 2. Graph Spec

- [x] 2.1 Add optional `workflow_graph` schema to `yaml-spec-template.md`.
- [x] 2.2 Extend `validate-workflow-spec.py` to validate `workflow_graph.schema_version`, `entrypoints`, `nodes`, `transitions`, and `templates_used`.
- [x] 2.3 Validate node id uniqueness, transition references, entrypoint references, and reachable graph shape.
- [x] 2.4 Allow graph nodes to use request-specific ids, roles, gates, input refs, output refs, and templates.
- [x] 2.5 Add valid and invalid graph spec fixtures.

## 3. Registry And Generated Assets

- [x] 3.1 Extend `registry` to support `agents`, `hooks`, and `runtime_assets` in addition to `commands` and `skills`.
- [x] 3.2 Validate that graph entrypoints and target outputs resolve to registry entries or declared deliverables.
- [x] 3.3 Update candidate generation expectations so generated assets must be declared by registry.
- [x] 3.4 Add S5 checks for undeclared target assets in the candidate bundle or target output.

## 4. Confirmation Gate

- [x] 4.1 Extend S3 readback requirements to include graph summary, target asset list, enabled capabilities, disabled capabilities, and managed apply policy.
- [x] 4.2 Extend draft/readiness validation so confirmation must name files that will be written.
- [x] 4.3 Add a negative fixture where confirmation is missing and target assets are not written.

## 5. Managed Apply Recovery

- [x] 5.1 Add before-snapshot capture for managed updates.
- [x] 5.2 Add `managed-rollback-manifest.json`.
- [x] 5.3 Add `managed-recover-instructions.md`.
- [x] 5.4 Add rollback safety rules for created, updated, conflicted, and user-modified files.
- [x] 5.5 Add S5 checks for recovery evidence.

## 6. Schema, Error, Remediation, Privacy

- [x] 6.1 Define common report fields: `schema_version`, `error_code`, `failure_kind`, and remediation fields.
- [x] 6.2 Add schema version checks for state, managed apply, S5 summary, host capability, and remediation reports.
- [x] 6.3 Centralize stable error codes for common failures.
- [x] 6.4 Add redaction utility and tests for token/password/key-like values.
- [x] 6.5 Ensure user-shareable reports use redacted content.

## 7. Agent Team Evidence

- [x] 7.1 Document that team plan is not execution evidence.
- [x] 7.2 Update S5 team checks so planned roles without output/events/join evidence cannot pass.
- [x] 7.3 Add a negative fixture where only `team-plan.json` exists.
- [x] 7.4 Validate that agent/team outputs affecting workflow semantics are reflected in accepted `workflow-spec.yaml`.

## 8. Regression

- [x] 8.1 Add a fixture where AI defines a non-S1-S6 target graph.
- [x] 8.2 Add a fixture where self-iteration is selected only when needed.
- [x] 8.3 Add a fixture where undeclared target assets are rejected.
- [x] 8.4 Run `validate-workflow.py`.
- [x] 8.5 Run the runtime smoke matrix.

- [x] 8.6 Run workflow graph spec validator fixtures.
- [x] 8.7 Run reporting/redaction unit test.
