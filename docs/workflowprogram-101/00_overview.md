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

## 下一章

继续看 [Ch1: 设计哲学](./01_product_thinking.md)。

