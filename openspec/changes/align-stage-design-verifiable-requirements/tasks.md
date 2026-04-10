## 1. Align Full Design Truth Sources

- [x] 1.1 Update [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md) so all supported intent flows, evidence ownership, stage exits, and approval semantics are normative at the top level.
- [x] 1.2 Update [/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md) so its details stay consistent with HighLevel and the runtime evidence model without introducing hidden product-level semantics.
- [x] 1.3 Update historical design review documents under [/mnt/d/Code/WorkflowProgram-CN/docs](/mnt/d/Code/WorkflowProgram-CN/docs) so previously resolved ambiguities are either archived or restated as closed decisions.

## 2. Close Routing, Discovery, and Design Gaps

- [x] 2.1 Update [/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py) and related route artifacts so `S0` ensures `target_root` exists before route completion and records whether it created the directory.
- [x] 2.2 Encode `S1` as `develop`-only in the machine-readable workflow contract where possible, and add deterministic checks for `workflow-spec.md` quality gates.
- [x] 2.3 Update approval handling, validators, and tests so `develop` cannot pass `S3` without resolved approval and manual vs auto approval remain distinguishable end to end.

## 3. Close Generation, Evidence, and Validation Gaps

- [x] 3.1 Tighten candidate generation and managed apply orchestration so the main product entry path invokes the existing scripts deterministically instead of relying only on prompt instructions.
- [x] 3.2 Update runtime evidence ownership across docs, templates, runner, and S5 judge so control-plane evidence and S5 verdict artifacts have one consistent ownership model.
- [x] 3.3 Extend validation and smoke coverage so the repo proves the intended contract on more than the current mock or adapter-heavy path.

## 4. Close Lessons and Intent-Flow Gaps

- [x] 4.1 Promote `audit`, `iterate`, and `validate` stage mappings into HighLevel and keep them aligned with LowLevel and route-intent behavior.
- [x] 4.2 Strengthen `S6` closure requirements and outputs so lessons, failure classification, and user-facing historical progress are more than prompt-level expectations.

## 5. Re-Audit Against the Full Requirement Matrix

- [x] 5.1 Add repository-level checks that fail fast when the full capability matrix drifts across HighLevel, LowLevel, templates, validators, or dist payloads.
- [x] 5.2 Re-run validation and smoke commands against the updated implementation and record each capability as `Satisfied`, `Partial`, or `Missing`.
- [x] 5.3 Update the implementation audit so the repo has a living conformance view against the OpenSpec requirement set.
