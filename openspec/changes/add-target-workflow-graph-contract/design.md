# Design

## Two-Layer Model

WorkflowProgram has two different graphs:

- Product lifecycle graph: `S0..S6`, owned by WorkflowProgram. It controls how WorkflowProgram clarifies, designs, writes, validates, and learns.
- Target workflow graph: request-specific `workflow_graph`, owned by the generated target workflow. It describes the actual business/domain workflow the user asked for.

The first graph remains fixed enough to keep the product verifiable. The second graph is flexible and may contain domain-specific nodes, branches, joins, handoffs, validation nodes, or self-iteration nodes.

## Artifact Chain

The semantic chain is:

```text
clarification package
  -> accepted workflow-spec.md
  -> accepted workflow-spec.yaml
  -> derived workflow-view.md / workflow-maintenance.md
  -> candidate bundle
  -> managed apply
  -> validation and recovery evidence
```

Rules:

- `workflow-spec.yaml` is the only machine-readable semantic source.
- `workflow-spec.md` is the human readback and approval artifact.
- `workflow-view.md` and `workflow-maintenance.md` must be generated from YAML and must not introduce new semantics.

## Proposed `workflow_graph`

Add optional top-level `workflow_graph` in `workflow-spec.yaml`:

```yaml
workflow_graph:
  schema_version: 1
  entrypoints:
    - name: reverse
      node: triage
  nodes:
    - id: triage
      template: analyze
      role: binary triage
      input_refs:
        - user_input.sample_path
      output_refs:
        - outputs/triage.md
      gate: none
      owner: analyst
    - id: static_analysis
      template: reverse_engineering
      role: static analysis
      input_refs:
        - outputs/triage.md
      output_refs:
        - outputs/static-report.md
      gate: reviewer_approval
      owner: reverser
  transitions:
    - from: triage
      to: static_analysis
      condition: binary_supported
  templates_used:
    - analyze
    - reverse_engineering
```

This section maps closely to current fields:

| Graph Field | Current Equivalent | Design Decision |
|---|---|---|
| `nodes` | `stages` | Similar shape, but target graph nodes are not bound to `S1..S6`. |
| `transitions` | `on_approve`, `on_reject`, `feedback`, `failure_recovery` | Make target graph edges explicit. |
| `entrypoints` | `test_contract.entry` and `registry` | Entry points must resolve to declared registry assets. |
| `templates_used` | `pattern`, `capability_discovery`, `agent_team_contract` | Optional reusable templates selected by AI/user. |
| `outputs` via `output_refs` | `test_contract.artifacts.deliverables` | Graph outputs must be covered by deliverables or explicit runtime evidence. |

## Registry Expansion

The existing registry only covers commands and skills. Extend it to cover:

- `commands`
- `skills`
- `agents`
- `hooks`
- `runtime_assets`

Generation rule:

- Runtime may generate only target assets declared in the accepted registry.
- Undeclared target assets must be rejected or reported before apply.
- Registry entries must map to candidate bundle paths and final target paths.

## Confirmation Gate

Before S4 writes anything, the S3 readback must explicitly list:

- The accepted target workflow graph.
- The accepted `workflow-spec.md` and `workflow-spec.yaml` paths.
- Target commands, skills, agents, hooks, and runtime files to be written.
- Enabled and disabled optional capabilities.
- Managed apply behavior and conflict/recovery policy.

Confirmation is not just a boolean flag. It must be backed by a concrete artifact list.

## Managed Apply Recovery

Managed apply should add recovery evidence without changing its current core safety model.

New outputs:

- `RUN_ROOT/outputs/managed-rollback-manifest.json`
- `RUN_ROOT/outputs/managed-recover-instructions.md`
- Optional before snapshots under `RUN_ROOT/outputs/managed-before/`

Behavior:

- Newly created files can be deleted during rollback if still unchanged.
- Updated files can be restored from before snapshots if still safe.
- Files changed by the user after apply must not be overwritten automatically; instructions must require manual review.

## Schema, Error, Remediation, And Privacy

Critical JSON outputs should include:

- `schema_version`
- stable `error_code` when failed or degraded
- `failure_kind`
- remediation fields when actionable
- redaction policy for sensitive values in user-facing reports

This applies at least to:

- `state.json`
- `events.jsonl`
- `managed-change-plan.json`
- `managed-change-result.json`
- `managed-rollback-manifest.json`
- `s5-validation-summary.json`
- `host-capability-report.json`
- `environment-remediation-report.json`

Privacy rule:

- Reports must redact known token/password/key patterns and sensitive environment values before they are written to user-shareable Markdown or JSON summaries.

## Agent Team Evidence Discipline

An agent/team plan is not execution evidence.

Rules:

- `team-plan.json` proves only planned roles.
- Execution requires role output files, dispatch events, join summary, or provider payload evidence.
- Any agent/team output that changes target workflow semantics must be reflected in accepted `workflow-spec.yaml`.
- S5 must not treat planned-but-unexecuted roles as successful participation.
