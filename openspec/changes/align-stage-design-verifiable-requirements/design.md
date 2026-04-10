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

**Non-Goals:**

- Redesign the `S0..S6` model.
- Replace the runner, S5 judge, or runtime host architecture.
- Introduce a new runtime outside the current `workflowprogram-*` and script stack.
- Resolve unrelated historical design debt outside the clarified decisions above.

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

## Risks / Trade-offs

- [Doc-first alignment can drift from code] → Follow up with validator and runner tasks that enforce the new rules where possible.
- [Creating `target_root` during `S0` may hide accidental path typos] → Require the creation result to be recorded in route/progress evidence so it is visible and reviewable.
- [Approval semantics may be partially encoded across docs and state] → Reuse `approval_status` and explicitly test `approved` vs `auto-approved`.
- [Making HighLevel more normative reduces flexibility] → Limit promotion to rules you explicitly approved, and keep LowLevel free to add detail that does not contradict HighLevel.

## Migration Plan

1. Update the HighLevel design to reflect the normative decisions.
2. Update the LowLevel design to align terminology, evidence ownership, and stage semantics with the HighLevel and runtime evidence spec.
3. Update validators, templates, and runner/judge behavior for rules that can be enforced automatically.
4. Add regression coverage for the clarified semantics.
5. Re-run repository and workflow validations after alignment.

## Open Questions

- None for this change. The previously ambiguous points were resolved by user decisions and the runtime evidence spec.
