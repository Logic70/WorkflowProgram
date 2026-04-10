# WorkflowProgram 101：把 Workflow 当成产品来设计

> 一套可维护的 workflow，不只是能生成文件，还要能说明怎么生成、怎么验证、怎么迭代。

这是 `WorkflowProgram-CN` 的章节版入门教程。

如果你只想快速扫一遍全貌，读单页版：

- [单页版教程](../workflowprogram-101.md)

如果你想按 `Workflow101` 的方式逐章理解，按下面顺序读：

| 章节 | 你会理解什么 | 关键词 |
|------|--------------|--------|
| [Ch0 全景](00_overview.md) | WorkflowProgram 到底在解决什么问题 | 产品化、控制面、交付物 |
| [Ch1 设计哲学](01_product_thinking.md) | 为什么 workflow 不是 prompt 集合 | 真源、控制面、验证、闭环 |
| [Ch2 三层目录模型](02_three_roots.md) | 为什么要区分 `PLUGIN_ROOT/TARGET_ROOT/RUN_ROOT` | 边界、证据、交付 |
| [Ch3 阶段模型](03_stage_model.md) | 为什么是 `S0..S6` | 职责、证据、回退 |
| [Ch4 编排主链](04_entry_and_runner.md) | 为什么要有 `workflow-entry.py` 和 `workflow-runner.py` | 确定性脚本链、程序控制面 |
| [Ch5 受控写入](05_managed_apply.md) | 为什么不能直接覆盖目标项目 | candidate、managed apply、冲突 |
| [Ch6 验证优先](06_validation.md) | 为什么生成链和验证链必须分开 | runner、judge、smoke |
| [Ch7 经验积累](07_lessons_and_constraints.md) | WorkflowProgram 如何学习 | lessons、constraints、S6 |
| [Ch8 迁移到你的项目](08_apply_to_your_project.md) | 如何用这套方法设计自己的 workflow | 设计清单、落地顺序 |

## 怎么读

建议顺序：

1. 先读 [Ch0 全景](00_overview.md)
2. 再读 [Ch1](01_product_thinking.md) 到 [Ch7](07_lessons_and_constraints.md)
3. 最后用 [Ch8](08_apply_to_your_project.md) 对照你自己的目标项目

如果你已经在读源码，这几个文件最值得配合着看：

1. [README.md](/mnt/d/Code/WorkflowProgram-CN/README.md)
2. [workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md)
3. [workflowprogram-stage-lowlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-lowlevel-design.md)
4. [workflow-entry.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-entry.py)
5. [workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py)
6. [workflow-s5-judge.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-s5-judge.py)

## 这套教程的目标

它不是教你背术语，而是帮你建立一个判断标准：

- 什么样的 workflow 只是 prompt 组合
- 什么样的 workflow 已经具备产品化能力
- WorkflowProgram 当前实现为什么会长成现在这样

