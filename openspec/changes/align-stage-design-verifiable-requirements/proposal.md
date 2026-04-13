## Why

The current stage design is close to aligned, but the full WorkflowProgram design still has no single, verifiable requirement decomposition that can be used to judge whether the implementation is actually complete and usable. Several decisions already landed in scripts or historical design notes, while others remain only in prose or prompt instructions, so the repo needs a full design-to-implementation audit contract instead of a narrow ambiguity checklist.

## What Changes

- Decompose the full WorkflowProgram design into OpenSpec capabilities and verifiable requirements, not just the previously clarified ambiguity points.
- Cover the full lifecycle:
  - routing and entry
  - requirement clarification
  - context discovery
  - design and contract generation
  - candidate generation and managed apply
  - runtime evidence and progress
  - validation and feedback loops
  - lessons, iteration, and intent flows
  - host capability discovery and bootstrap
  - optional agent-team orchestration
  - installation and distribution contracts
- Normalize stage-level evidence ownership using the runtime evidence model as the source for `state.json` and `events.jsonl`.
- Promote explicit normative decisions for:
  - `target_root` readiness at S0
  - `S1` applying only to `develop`
  - mandatory approval at S3, with distinct records for manual vs auto approval
  - intent-to-stage mappings for `audit`, `iterate`, and `validate`
- Produce an implementation-conformance audit so the current repo can be judged against these requirements as `satisfied / partial / missing`.
- Add pending requirement families for:
  - identifying domain-specific professional capabilities required by a generated workflow
  - checking whether required skills, MCP servers, or external tools already exist on the host
  - installing or configuring missing host capabilities only through explicit, reviewable bootstrap steps
  - expressing optional agent-team topology and verification rules as a machine-checkable contract

## Capabilities

### New Capabilities
- `workflow-routing-and-entry`: Defines the routing contract, supported entry modes, target resolution, and S0 evidence requirements.
- `workflow-requirement-discovery`: Defines `S1` requirement clarification behavior, quality gates, and scope.
- `workflow-context-and-design`: Defines `S2` context discovery and `S3` design-contract generation requirements.
- `workflow-managed-generation`: Defines `S4` candidate generation, managed apply, runner integration, and conflict handling.
- `workflow-runtime-evidence-and-progress`: Defines runtime evidence, stage progress, and control-plane proof requirements across stages.
- `workflow-validation-feedback`: Defines `S5` workflow validation, test-contract consumption, smoke evidence, and feedback-loop behavior.
- `workflow-lessons-and-intent-flows`: Defines `S6` lessons closure and the normative intent-to-stage mappings.
- `workflow-distribution-contract`: Defines source/dist/release installation and canonical plugin payload expectations.
- `workflow-stage-contracts`: Defines normative, stage-by-stage requirements for `S0..S6`, including evidence ownership, approval gates, stage entry and exit conditions, and required outputs.
- `workflow-intent-flows`: Defines normative intent-to-stage mappings and stage applicability rules, including `develop`, `audit`, `iterate`, and `validate`.
- `workflow-host-capability-bootstrap`: Defines how WorkflowProgram discovers domain-specific professional capability needs, checks host readiness, and boots missing skills / MCP / tools through explicit approval and auditable evidence.
- `workflow-agent-team-orchestration`: Defines the optional contract for team-style agent orchestration, including role declarations, fan-out limits, join policy, ownership, and runtime evidence.

### Modified Capabilities

## Impact

- Affects design truth sources in [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md), [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md), and historical design references under [/mnt/d/Code/WorkflowProgram-CN/docs](/mnt/d/Code/WorkflowProgram-CN/docs).
- Affects runtime evidence and validation truth sources in [/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md), [/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py), [/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-spec.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-spec.py), and [/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-s5-judge.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-s5-judge.py).
- Affects future task planning, audit outputs, and conformance review artifacts under [/mnt/d/Code/WorkflowProgram-CN/openspec](/mnt/d/Code/WorkflowProgram-CN/openspec).
- Does not directly finish all implementation gaps in this change; this change defines the full requirement contract and the audit baseline implementation must satisfy.
