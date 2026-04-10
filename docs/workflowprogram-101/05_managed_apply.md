# Ch5: 受控写入 — 为什么不能直接覆盖 TARGET_ROOT/.claude

> 能写进去不代表应该直接写进去。

## 5.1 直接写目标项目会出什么问题

如果 workflow 直接写 `TARGET_ROOT/.claude/`，最容易出现 3 类风险：

1. 覆盖用户手工维护的文件
2. 不知道哪些文件是工具托管的
3. 发生冲突时无法保留中间态证据

所以 `WorkflowProgram` 当前实现坚持 candidate -> managed apply。

## 5.2 当前写入链

关键产物包括：

- `RUN_ROOT/outputs/candidate/.claude/`
- `RUN_ROOT/outputs/managed-change-plan.json`
- `RUN_ROOT/outputs/managed-change-result.json`
- `TARGET_ROOT/.workflowprogram/managed-files.json`

真实链路是：

```text
AI 生成候选 -> plan -> apply-staged -> TARGET_ROOT/.claude/*
```

而不是：

```text
AI 直接覆盖 -> TARGET_ROOT/.claude/*
```

## 5.3 为什么这很重要

这一层带来的好处是：

- 可以提前发现冲突
- 可以知道哪些文件是 managed
- 可以保留候选和冲突副本
- 可以把“写入”从“生成”里解耦

这对后续验证和审计都很关键。

## 5.4 读当前实现时看哪里

想理解这层设计，优先看：

1. [managed-assets.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/managed-assets.py)
2. [workflow-entry.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-entry.py)
3. [README.md](/mnt/d/Code/WorkflowProgram-CN/README.md) 里的目标资产更新契约

## 5.5 提炼模板

只要你的 workflow 会改用户项目，就默认采用：

1. 先生成候选
2. 再做变更计划
3. 再执行受控应用
4. 冲突时保留证据，不静默覆盖

这是 workflow 工程化的一个硬分水岭。

## 下一章

继续看 [Ch6: 验证优先](./06_validation.md)。

