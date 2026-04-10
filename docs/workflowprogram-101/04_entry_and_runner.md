# Ch4: 编排主链 — 为什么需要 workflow-entry.py 和 workflow-runner.py

> 如果顺序只是写在 prompt 里，那它本质上还是建议，不是程序。

## 4.1 为什么不能只靠 skill 文本编排

skill 文本擅长定义语义步骤，但不擅长做这些事：

- 确保脚本执行顺序固定
- 确保状态真的落盘
- 确保边界检查真的执行
- 确保失败时有一致的结构化结果

所以 `WorkflowProgram` 把编排拆成两层：

- `workflow-entry.py`
  - 产品入口 wrapper
- `workflow-runner.py`
  - 程序控制面 runner

## 4.2 workflow-entry.py 负责什么

[workflow-entry.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-entry.py) 负责把 prompt 层约定收敛成固定脚本链。

当前 `run` 子命令会固定调用：

1. `validate-workflow-spec.py`
2. `generate-workflow-view.py`
3. `managed-assets.py plan/apply-staged`
4. `workflow-runner.py run`
5. `validate-run-state.py`

这意味着主入口已经不再依赖“模型记得下一步该做什么”。

## 4.3 workflow-runner.py 负责什么

[workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py) 负责：

- 状态转移
- 边界校验
- 证据落盘
- 最小运行约束检查

但它不负责：

- workflow 级最终判定
- S5 主 judge 语义

这条边界非常重要。

## 4.4 当前实现的价值

有了这两层，`workflowprogram-develop` 不再只是“一个很长的说明书”，而是一条确定性的产品入口链。

你可以把它记成：

- `entry` 负责串脚本
- `runner` 负责控制面
- `validate` 负责判定

## 4.5 提炼模板

当你的 workflow 开始涉及：

- 多阶段切换
- 目标项目写入
- 运行证据
- 结构化验证

就应该考虑把“编排逻辑”从 prompt 里拆到确定性脚本里。

## 下一章

继续看 [Ch5: 受控写入](./05_managed_apply.md)。

