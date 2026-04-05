---
name: workflowprogram-iterate
description: Generate workflow improvement proposals from lessons and current workflow state
version: 1.0.0
disable-model-invocation: true
---

面向 `TARGET_ROOT` 的工作流迭代主入口。基于 `lessons.md`、当前 workflow 状态和审计结果生成改进草案。

## When To Use

- 从 `lessons.md` 提炼可执行改进项
- 为当前 workflow 生成审批优先的迭代草案
- 将经验沉淀转化为结构化优化建议

## Core Rules

- 默认输出草案，不应直接应用结构性改动。
- 读取经验时优先关注近期 lessons 和未提取规则。
- 需要区分：自动可修复项、需要审批的结构改动、可提取为规则的内容。
- 必要时结合 `workflow-audit` 和 `validate-file` 交叉验证。

## Step 1: Resolve Target

1. 确认 `TARGET_ROOT` 和目标 workflow 路径。
2. 读取 `lessons.md`、现有 `.claude/` 资产和最近的审计结果。
3. 标记可直接处理与需审批的事项。

## Step 2: Build Proposal

1. 归类问题：格式、结构、模式、规则。
2. 输出每项提案的原因、影响和目标文件。
3. 对需要审批的项保留 draft 模式。

## Step 3: Prepare Next Actions

1. 指出哪些项建议先做 `workflowprogram-validate`。
2. 指出哪些项适合提炼到 rules 层。
3. 生成适合 CLI 阅读的提案摘要。

## Output

输出应包含：

- 分析摘要
- 提议清单
- 需要审批的变更
- 可提取规则候选项
