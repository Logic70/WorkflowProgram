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
- [workflowprogram-101-html/index.html](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-101-html/index.html)
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
- `workflow-spec.yaml` 是机器语义真源与运行态地图，不是完整设计文档；完整设计推理由 S3 设计源承载。
- `state.json` 与 `events.jsonl` 属于运行时控制面证据，由 runner 产出，S5 只消费。
- `target_root` 在 `S0` 准出前必须存在；若不存在，由执行链创建并记录。
- `S1` 仅属于 `develop` 主链。
- `S3` 必须经过审批 gate，且必须区分 `approved` 与 `auto-approved`。
- 阶段模型固定为显式 `stage_slot: S1..S6`，不再允许按顺序隐式推导。
- `stage_slot: S1..S6` 只约束 WorkflowProgram 自身控制面；生成后的目标工作流可通过 `workflow_graph` 声明自己的业务节点图。
- 产品主入口的确定性脚本链为 `workflow-entry.py -> managed-assets.py -> workflow-runner.py -> validate-run-state.py`。
- 目标工作流 runtime 的交付模式固定为 `generated_runtime_contract.mode = shared-control-plane-wrapper`。
- S1/S2/S3 的需求转化链为 `target-requirements.yaml -> target-context-findings.yaml -> target-design-overview.md / target-design-detail.md -> workflow-spec.yaml -> target-traceability-matrix.json`。
- `workflow-spec.md` 是用户回读，`workflow-view.md` 与 `workflow-maintenance.md` 是从 YAML 派生的报告，`target-design-detail.md` 才是目标工作流低层设计源。
- 复杂目标业务节点应升级为 `outputs/stages/target-node-designs/<node-id>.md`，而不是拆成新的 WorkflowProgram `S1..S6`；node 与 agent 不要求一一对应，且 node-design 必须通过内容校验证明与 `workflow_graph.nodes[*]` 的 owner、template、gate、input/output、loop policy 一致。
- completed develop 需要把 target design source 归档到 `TARGET_ROOT/.workflowprogram/design/source/**`，供后续修改、审计、validate 与 publish 使用。
- managed apply 必须保留 `managed-rollback-manifest.json` 与 `managed-recover-instructions.md`，并在共享报告中包含 schema/remediation 字段。
- 宿主专业能力必须通过 `host_capabilities` 声明，readiness / bootstrap 证据只写入 `RUN_ROOT`。
- `project_local` bootstrap 只允许写入 `TARGET_ROOT/.workflowprogram/bootstrap/**`，且应优先通过声明式 `bootstrap.assets` 生成可复用配置 / wrapper / marker 资产，并同步落 target bootstrap manifest。
- 若工作流启用 `capability_discovery`，则必须在 `RUN_ROOT` 生成 `host-capability-candidates.json` 与 `host-bootstrap-instructions.md`，用于在 `host_capabilities` 最终定稿前给出候选能力和精确人工指引。
- 显式 team orchestration 必须通过 `agent_team_contract` 声明；普通 subagent 不自动等于 team flow。
- Ralph-style 持续执行只能作为 `workflow_graph.nodes[*].loop_policy` 的目标节点策略；它不替换 WorkflowProgram 自身 `S1..S6`，且成功必须由 verifier/test 证据证明。
