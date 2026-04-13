# Ch0: 全景 — WorkflowProgram 到底在解决什么问题

> WorkflowProgram 不是为了“帮你多写几个 prompt 文件”，而是为了把 workflow 做成可交付、可验证、可迭代的产品。

## 场景引入

很多团队开始做 Claude Code workflow 时，第一步通常是：

- 写一个 `SKILL.md`
- 再补几个 `agents/*.md`
- 最后把 `settings.json` 手工改一下

这样做能跑，但很快会碰到更难的问题：

- 目标项目到底允许被改哪些文件
- 这次运行修改了什么，证据在哪
- workflow 失败时，问题在设计还是实现
- 下一次如何避免重复犯错

`WorkflowProgram` 就是为了解这类问题存在的。

## 它实际在解决哪些编排老问题

把常见编排问题摊开看，`WorkflowProgram` 主要在补这 8 个缺口：

| 问题 | 如果不解决会怎样 | 当前设计怎么处理 |
|------|------------------|------------------|
| 缺少统一真源 | 文档、prompt、实现各说各话 | 把执行语义收口到 `workflow-spec.yaml` |
| 编排顺序不稳定 | 模型可能跳步骤、漏步骤、重复步骤 | 用 `workflow-entry.py` 固定主链，用 `workflow-runner.py` 固定阶段流转 |
| 写入边界不清 | 很容易直接污染目标项目 | 先写 `RUN_ROOT/outputs/candidate/.claude/`，再做 managed apply |
| 证据留存不足 | 失败后无法复盘，也无法做自动验证 | 在 `RUN_ROOT` 留 `context/state/events/transcript/report` |
| 设计和执行耦合 | 很难分清“设计错了”还是“执行偏了” | 把 `spec`、runner、judge、smoke 分层 |
| 验证只看退出码 | 很难判断 workflow 是否真的按约束执行 | 用 `runtime_contract + test_contract + S5 judge` 做 verdict |
| 经验无法回流 | 下一轮还是从零开始，持续重复犯错 | 用 `S6` 生成 `s6-lessons-delta.md` 并沉淀到规则 |
| 入口意图不稳定 | 同类请求会落到不同 skill，行为漂移 | 用 `workflowprogram-orchestrate` 和 `route-intent.py` 收口入口 |

换句话说，`WorkflowProgram` 不是只想“生成文件”，而是想把 workflow 编排里最常见的失控点变成明确的设计对象。

## 它交付什么

它交付的不是业务代码，而是目标项目中的 workflow 资产：

- `TARGET_ROOT/.claude/skills/*`
- `TARGET_ROOT/.claude/agents/*`
- `TARGET_ROOT/.claude/rules/*`
- `TARGET_ROOT/.claude/settings.json`

同时它还交付一套运行和治理能力：

- candidate -> managed apply 的写入链
- `RUN_ROOT` 运行证据
- workflow 级验证结论
- lessons 和约束候选

## 先看主链

把它抽象成一句话，就是：

```text
用户需求 -> 规格 -> 候选资产 -> 受控写入 -> 运行验证 -> 经验沉淀
```

当前实现中，对应的核心载体是：

- `workflowprogram-orchestrate`
- `workflowprogram-develop`
- `workflow-entry.py`
- `workflow-runner.py`
- `workflowprogram-validate`
- `validate-lessons-delta.py`

## 你应该先建立的直觉

理解 WorkflowProgram 时，先记住 4 句话：

1. workflow 是产品，不是 prompt 集合
2. 设计、执行、验证、迭代不是一回事
3. 目标写入必须受控，不能直接覆盖
4. 一次运行必须留下证据，不然就无法复盘

如果把这 4 句话反过来看，其实就是编排工作流最常见的 4 类故障：

- 没把 workflow 当产品，最后只有 prompt，没有控制面
- 没分开设计、执行、验证、迭代，最后所有问题混在一次对话里
- 没有受控写入，最后目标仓直接被污染
- 没有运行证据，最后只能靠记忆和聊天记录猜问题

## 下一章

继续看 [Ch1: 设计哲学](./01_product_thinking.md)。
