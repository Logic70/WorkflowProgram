# WorkflowProgram 文档状态索引

## 当前生效设计真源

以下文档构成当前运行与验证口径的真源：

- [workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md)
- [workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md)
- [workflowprogram-stage-consistency-check.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-consistency-check.md)

## Supporting Doc

以下文档为当前真源提供补充定义，但不单独决定阶段职责：

- [phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md)
- [workflowprogram-capability-matrix.json](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-capability-matrix.json)
- [workflowprogram-101.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-101.md)
- [workflowprogram-101/index.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-101/index.md)

## 历史追溯文档

以下文档保留为设计演进记录，不再充当当前运行时真源：

- [workflowprogram-skills-first-redesign.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-skills-first-redesign.md)
- [phase-02-step-01-entry-boundary-audit.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-02-step-01-entry-boundary-audit.md)
- [phase-03-step-01-runtime-validation-audit.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-01-runtime-validation-audit.md)
- [phase-04-implementation-plan.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-04-implementation-plan.md)

## 已关闭决策

- `workflow-spec.yaml.intent_flows` 是 `develop / audit / iterate / validate` 的机器可读真源。
- `state.json` 与 `events.jsonl` 属于运行时控制面证据，由 runner 产出，S5 只消费。
- `target_root` 在 `S0` 准出前必须存在；若不存在，由执行链创建并记录。
- `S1` 仅属于 `develop` 主链。
- `S3` 必须经过审批 gate，且必须区分 `approved` 与 `auto-approved`。
- 阶段模型固定为显式 `stage_slot: S1..S6`，不再允许按顺序隐式推导。
- 产品主入口的确定性脚本链为 `workflow-entry.py -> managed-assets.py -> workflow-runner.py -> validate-run-state.py`。
