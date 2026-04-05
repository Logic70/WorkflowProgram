# WorkflowProgram Stage 设计一致性校验报告

## 1. 校验目的

本报告用于验证以下文档的前后文逻辑一致性：

- [workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md)
- [workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md)

并与当前实现基线对齐（`workflowprogram-*` skills、`/develop`、`managed-assets.py`、`RUN_ROOT` 证据模型）。

## 2. 校验结果总览

| 校验项 | 结果 | 说明 |
|---|---|---|
| Stage 命名与顺序一致性 | PASS | 两份文档均采用 `S0..S6` |
| 路径模型一致性 | PASS | `PLUGIN_ROOT/TARGET_ROOT/RUN_ROOT` 定义一致 |
| 安装与分发契约一致性 | PASS | `dist/plugin` 被定义为 canonical 载荷目录，支持 Source Build 与 GitHub Release 两种通道 |
| 入口契约一致性 | PASS | 自然语言仅由 `workflowprogram-orchestrate` 承接 |
| 输出结论枚举一致性 | PASS | `PASS/WARN/FAIL/ENVIRONMENT-SKIP` 已统一 |
| state 字段约束完整性 | PASS | Lowlevel 定义了固定字段与枚举 |
| artifact 字段约束完整性 | PASS | `kind/root/producer/status` 均已枚举化 |
| Stage 间 I/O 依赖闭合 | PASS | `S1->S2->S3->S4->S5->S6` 无未定义依赖 |
| Stage 准出可验证性 | PASS | 每个 Stage 已补充证据路径和可验证检查条目 |
| 进展与关键节点可视化契约 | PASS | 增加 `current-progress/milestones/user-progress` 三类进展资产 |
| 与现有实现贴合度 | PASS | 未引入强依赖的新外部运行时 |
| 设计与实现差距可见性 | WARN | spec 控制面是目标架构，仍需后续脚本级强化 |

## 3. Stage 依赖链检查

### 3.1 主链（develop）

- `S0` 输出 `intent/target_root`，可驱动 `S1`。
- `S1` 输出 `workflow-spec.md`，可驱动 `S2`。
- `S2` 输出上下文结论，作为 `S3` 设计输入。
- `S3` 输出 `workflow-spec.yaml` 与 `workflow-view.md`，可驱动 `S4`。
- `S4` 输出 candidate 与 managed 结果，可驱动 `S5`。
- `S5` 输出验证结论，可驱动 `S6` 闭环。

### 3.2 其他意图链

- `audit`: `S0 -> S5(审计模式) -> S6`
- `validate`: `S0 -> S5 -> S6(可选)`
- `iterate`: `S0 -> S6(提案模式) -> S5(可选)`

结论：意图链无循环死锁，且准出目标可判定。

## 4. state/artifact 冲突检查

### 4.1 已消解冲突

- 冲突 C1：验证结论枚举在高低层文档不一致。  
  处理：Lowlevel 已统一为 `PASS/WARN/FAIL/ENVIRONMENT-SKIP`。

- 冲突 C2：`producer` 无约束可能导致命名漂移。  
  处理：Lowlevel 规定 `producer` 必须为 `S0..S6`。

- 冲突 C3：state 直接承载文件内容风险高。  
  处理：Highlevel/Lowlevel 统一为“state 追踪引用，文件内容落盘”。

- 冲突 C4：`dist/plugin` 被表述为“唯一安装路径”，与 GitHub 包分发场景冲突。  
  处理：改为“仓库内 canonical 载荷目录”；安装可通过任意同构目录并用 `--plugin-dir` 加载。

- 冲突 C5：Stage 目标与输出缺少可判定标准。  
  处理：Highlevel 增加 Stage 验收矩阵，Lowlevel 为每个 Stage 增加证据路径与可验证检查。

### 4.2 非阻断待实现项

- 待实现 R1：`workflow-spec.yaml` 的字段约束尚未完全脚本化校验。
- 待实现 R2：`producer/kind/status` 枚举尚未在生成链路强制执行。
- 待实现 R3：Stage 转移规则目前主要由 prompt/流程约定保证，尚未完全自动化调度。

## 5. 结论

当前文档级设计已经满足“前后文逻辑一致、Stage 交互无定义冲突、state 与路径模型统一”的要求。  
剩余差距集中在“把文档约束进一步工程化为脚本校验和执行约束”，属于后续实施问题，不影响本轮设计文档成立。
