# Ch6: 验证优先 — 为什么生成链和验证链必须分开

> 生成者最不适合担任自己的最终裁判。

## 6.1 为什么验证必须独立出来

如果“生成”和“验证”是同一个角色负责，通常会有两个问题：

- 生成成功就被误当成验证通过
- 最终失败时无法区分是设计缺陷、实现缺陷还是环境缺陷

所以 `WorkflowProgram` 当前把验证单独放在 `S5`。

## 6.2 当前实现的三层验证

验证不是一层，而是三层：

- `workflow-runner.py`
  - 控制面硬约束
  - 例如边界、证据、失败枚举
- `workflowprogram-validate`
  - workflow 级主 judge
  - 消费 `test_contract`
- `runtime_smoke.py`
  - 动态 harness
  - 补运行态证据，不替代主 judge

## 6.3 当前实现里的核心分工

一句话记忆：

- runner 决定“能不能这样跑”
- judge 决定“这样跑算不算通过”
- smoke 决定“有没有补到动态证据”

这条边界，是 `WorkflowProgram` 当前实现最关键的设计之一。

## 6.4 最终看什么文件

这层最重要的输出是：

- `RUN_ROOT/validation-runtime-report.md`
- `RUN_ROOT/outputs/stages/s5-validation-summary.json`

而控制面证据主要是：

- `RUN_ROOT/context.json`
- `RUN_ROOT/state.json`
- `RUN_ROOT/events.jsonl`

这两类文件不要混着理解。

## 6.5 提炼模板

只要 workflow 稍微复杂一点，最好至少拆出：

1. 执行约束层
2. 判定层
3. 动态证据层

把这三层揉在一起，后面几乎一定会难以扩展。

## 下一章

继续看 [Ch7: 经验积累](./07_lessons_and_constraints.md)。

