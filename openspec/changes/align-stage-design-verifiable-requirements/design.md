## Context

The current design baseline lives across three sources:

- [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md)
- [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md)
- [/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md)

The HighLevel and LowLevel stage documents are broadly compatible, but several normative decisions were either implicit or split across documents:

- ownership of `state.json` and `events.jsonl`
- whether `target_root` must exist at `S0` exit
- whether `S1` applies to non-`develop` intents
- whether `S3` approval is mandatory and how auto approval differs from manual approval
- whether `audit`, `iterate`, and `validate` stage flows belong in the HighLevel contract
- whether generated target workflows must ship their own deterministic runtime entry and state/control-plane mechanism instead of stopping at design assets
- how domain-specific professional capabilities should be discovered, checked, and bootstrapped
- whether advanced multi-agent team orchestration is a first-class workflow contract or only prompt advice

Current implementation already encodes part of the intended behavior:

- [workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py) owns control-plane state, required evidence checks, and `approval_status`
- [validate-workflow-spec.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-spec.py) validates `runtime_contract` and `test_contract`
- [workflow-s5-judge.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-s5-judge.py) consumes `test_contract` and `runtime_contract` for S5 judgment
- [route-intent.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/route-intent.py) defines the intent router and entry-skill mapping

This change turns those decisions into a verifiable requirement contract that can drive later document edits, validator changes, and tests.

## Goals / Non-Goals

**Goals:**

- Make the stage contract verifiable instead of leaving key semantics in review notes.
- Use the runtime evidence spec as the source for `state.json`, `events.jsonl`, `transcript.md`, and `validation-runtime-report.md` definitions.
- Promote user-confirmed rules into normative requirements:
  - `S0` exits only after `target_root` exists
  - `S1` applies only to `develop`
  - `S3` approval is mandatory before `S4`
  - manual approval and auto approval remain distinguishable
  - `audit`, `iterate`, and `validate` stage chains appear in HighLevel
- Produce implementation tasks that are small, ordered, and testable.
- Make generated target workflows inherit the same deterministic runtime-control-plane discipline that WorkflowProgram now uses for itself.
- Turn host capability discovery/bootstrap and agent-team support into verifiable requirement families, even if implementation follows later.

**Non-Goals:**

- Redesign the `S0..S6` model.
- Replace the runner, S5 judge, or runtime host architecture.
- Force generated workflows to reuse the exact same script filenames if an equivalent deterministic runtime contract is cleaner for the target workflow.
- Introduce a new runtime outside the current `workflowprogram-*` and script stack.
- Resolve unrelated historical design debt outside the clarified decisions above.
- Automatically install arbitrary host tools without an explicit bootstrap boundary.

## Decisions

### 1. Runtime evidence definitions come from the Phase 3 evidence spec

`state.json` and `events.jsonl` are defined by the runtime evidence model in [/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md). They are control-plane/runtime evidence files that S5 consumes, not S5-owned artifacts.

Rationale:

- LowLevel already assigns them to runner-owned evidence and `runtime_contract.required_evidence`.
- Current implementation checks them as required evidence in [workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py).
- Treating them as purely S5-owned creates ownership drift with the runtime evidence spec and current code.

Alternative considered:

- Keep `state.json` and `events.jsonl` as S5 minimum evidence in HighLevel without changing ownership semantics.
- Rejected because it preserves ambiguity about who produces them and who validates their existence.

### 2. `S0` exits only after `target_root` exists

`S0` SHALL resolve `target_root` to an absolute path and ensure the directory exists before stage completion. If the directory does not exist, the system SHALL create it and record that outcome in route/progress evidence.

Rationale:

- You explicitly chose “准出需要已存在，如果不存在就要创建”.
- Downstream boundary and writable checks assume a materialized target root.
- This makes `S0` a reliable hand-off point for the rest of the flow.

Alternative considered:

- Only require that the path be resolvable to an absolute path.
- Rejected because it leaves directory creation behavior implicit and shifts a routing concern into later stages.

### 3. `S1` is specific to `develop`

`S1` SHALL apply only to the `develop` intent. `audit`, `iterate`, and `validate` flows SHALL bypass `S1` unless a future requirement explicitly extends them.

Rationale:

- LowLevel already treats `S1` as `intent=develop`.
- The other intent paths do not require drafting a fresh `workflow-spec.md` as their normative first step.

Alternative considered:

- Define a generic `S1` for all intents.
- Rejected because it weakens intent-specific flow semantics and makes non-develop flows less testable.

### 4. `S3` approval is mandatory and approval provenance must remain explicit

The `develop` path SHALL not proceed from `S3` to `S4` until approval is resolved. The recorded approval outcome SHALL distinguish manual approval from automatic approval.

Rationale:

- You explicitly required mandatory approval.
- Current implementation already differentiates `approved` and `auto-approved` in runner state.
- Keeping provenance explicit supports auditability and later judge/trace validation.

Alternative considered:

- Treat approval as optional or collapse manual and automatic approval into a single status.
- Rejected because it removes a required gate and loses execution provenance.

### 5. HighLevel owns the normative intent-to-stage mappings

HighLevel SHALL explicitly publish the stage mappings for `develop`, `audit`, `iterate`, and `validate`. LowLevel may elaborate node structure and validation details, but not be the only place where those mappings exist.

Rationale:

- Intent-to-stage flow is a product-level contract, not only an implementation detail.
- Leaving non-`develop` paths only in LowLevel makes the top-level design incomplete.

Alternative considered:

- Keep non-`develop` stage chains only in LowLevel.
- Rejected because it hides user-visible workflow semantics in the implementation layer.

### 6. Verification must span docs, validators, and runtime behavior

This change is only complete when the requirement contract is reflected in:

- HighLevel / LowLevel document wording
- machine-checkable spec validation where practical
- runner or judge behavior where the rule is executable
- regression coverage for the clarified semantics

Rationale:

- A document-only fix would drift again.
- Current implementation already has a validator/runner/judge structure suitable for enforcing part of the contract.

### 7. Domain-specific professional capability dependencies are host contracts, not hidden prompt hints

If a generated workflow depends on specialized tooling or integrations, WorkflowProgram SHALL model that dependency explicitly as a host capability requirement. This includes Codex skills, MCP servers, external binaries, or licensed tools that are required for the workflow to be genuinely usable.

Rationale:

- Today the implementation can declare `agent_refs` and `skills`, but it cannot prove the host actually has the professional capability needed for a domain workflow.
- Your reverse-engineering example is exactly this gap: a workflow that references reverse-engineering steps is not actually usable if the host lacks the expected skill or MCP integration.
- Host setup should not be smuggled into `TARGET_ROOT` asset generation.

Alternative considered:

- Keep specialized dependencies as free-form design notes or prompt text.
- Rejected because that makes “workflow ready” unverifiable and hides a major usability gap.

### 8. Generated target workflows SHALL ship deterministic runtime orchestration as a first-class product capability

WorkflowProgram SHALL not stop at generating declarative design assets for target workflows. If a generated workflow claims staged execution, approval gates, runtime evidence, or testable control-plane behavior, the delivered target workflow SHALL also include its own deterministic runtime entry path and machine-enforced state/control-plane transition mechanism, or an explicitly equivalent mechanism with the same guarantees.

Rationale:

- WorkflowProgram itself now uses a deterministic entry wrapper plus runner-backed control plane; generated workflows should not regress to prompt-only execution if they are meant to be equally auditable and repeatable.
- A target workflow that only ships commands/skills plus design docs is still missing the most important execution guarantee: fixed invocation order and persisted state transitions.
- This is now the highest-priority pending requirement because it directly determines whether generated workflows are truly usable as products rather than only as design bundles.

Alternative considered:

- Keep generated workflows declarative only and treat deterministic runtime control as a future optional enhancement.
- Rejected because it leaves a major product gap between WorkflowProgram's own execution model and the workflows it generates.

### 9. Agent-team orchestration is an optional advanced contract, not a default execution model

WorkflowProgram SHALL support agent-team orchestration only as an explicit opt-in capability with a machine-readable contract for team roles, limits, and join behavior. It SHALL not be inferred from prose alone.

Rationale:

- The current system already benefits from deterministic stage contracts and clear evidence ownership; implicit team behavior would weaken that.
- Team support is valuable for certain domains, but only if the topology and validation rules are explicit enough to audit.

Alternative considered:

- Allow team support only as prompt discipline without a contract.
- Rejected because it would be impossible to validate whether the declared team behavior actually occurred.

## Risks / Trade-offs

- [Doc-first alignment can drift from code] → Follow up with validator and runner tasks that enforce the new rules where possible.
- [Creating `target_root` during `S0` may hide accidental path typos] → Require the creation result to be recorded in route/progress evidence so it is visible and reviewable.
- [Approval semantics may be partially encoded across docs and state] → Reuse `approval_status` and explicitly test `approved` vs `auto-approved`.
- [Making HighLevel more normative reduces flexibility] → Limit promotion to rules you explicitly approved, and keep LowLevel free to add detail that does not contradict HighLevel.
- [Host bootstrap can mutate the developer environment] → Model it as a separate, approval-gated contract and evidence trail rather than a hidden side effect of `develop`.
- [Agent-team support can add validation complexity] → Keep it opt-in and require explicit topology plus runtime evidence before calling it supported.

## Migration Plan

1. Update the HighLevel design to reflect the normative decisions.
2. Update the LowLevel design to align terminology, evidence ownership, and stage semantics with the HighLevel and runtime evidence spec.
3. Update validators, templates, and runner/judge behavior for rules that can be enforced automatically.
4. Add regression coverage for the clarified semantics.
5. Re-run repository and workflow validations after alignment.
6. Add the highest-priority pending requirement family for deterministic target-workflow runtime orchestration, then audit the current implementation against it before the lower-priority expansion families.
7. Add pending requirement families for host capability bootstrap and agent-team orchestration, then audit the current implementation against them.

## Open Questions

- The new target-runtime, host-capability, and agent-team requirement families are intentionally added as pending implementation targets; detailed schema and runtime evidence formats remain future design work.
